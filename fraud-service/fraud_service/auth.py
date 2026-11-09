"""Metadata handling for FraudService calls: API keys, roles and request ids.

BR-FRD-04 (x-api-key and roles) and BR-FRD-05 (x-request-id in trailing metadata).
Health check and reflection are not guarded.
"""

import os
import threading
import uuid

import grpc

from fraud_service import buggy

FRAUD_METHOD_PREFIX = "/fraud.v1.FraudService/"

_KEYS = {
    os.getenv("FRAUD_API_KEY_WALLET", "dev-wallet-key"): "wallet",
    os.getenv("FRAUD_API_KEY_MONITOR", "dev-monitor-key"): "monitor",
}

# Role -> allowed method names; None means every method.
ROLE_METHODS: dict[str, frozenset[str] | None] = {
    "wallet": None,
    "monitor": frozenset({"WatchRiskEvents", "GetDecision"}),
}

_local = threading.local()


def role_for_key(key: str | None) -> str | None:
    return _KEYS.get(key) if key else None


def current_request_id() -> str:
    """The x-request-id of the call being served in this thread."""
    return getattr(_local, "request_id", "")


def _check_access(key: str | None, method: str) -> tuple[grpc.StatusCode, str] | None:
    """None if allowed, else (status code, message)."""
    role = role_for_key(key)
    if role is None:
        if key and buggy.enabled("BUG-17"):  # planted: wrong status code for an unknown key
            return grpc.StatusCode.PERMISSION_DENIED, "unknown x-api-key"
        return grpc.StatusCode.UNAUTHENTICATED, "missing or unknown x-api-key"
    allowed = ROLE_METHODS[role]
    if allowed is not None and method not in allowed:
        return grpc.StatusCode.PERMISSION_DENIED, f"role {role} may not call {method}"
    return None


class AuthInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        full_method = handler_call_details.method
        if handler is None or not full_method.startswith(FRAUD_METHOD_PREFIX):
            return handler

        metadata = dict(handler_call_details.invocation_metadata or ())
        method = full_method[len(FRAUD_METHOD_PREFIX):]
        request_id = metadata.get("x-request-id") or str(uuid.uuid4())
        denied = _check_access(metadata.get("x-api-key"), method)
        return _wrap(handler, request_id, denied)


def _wrap(handler, request_id: str, denied):
    """Same kind of handler, with request id and access check in front of the behaviour."""

    def prepare(context):
        _local.request_id = request_id
        if denied or not buggy.enabled("BUG-19"):  # planted: id lost on successful calls
            context.set_trailing_metadata((("x-request-id", request_id),))
        if denied:
            context.abort(*denied)

    def unary(behaviour):
        def wrapped(request_or_iterator, context):
            prepare(context)
            return behaviour(request_or_iterator, context)

        return wrapped

    def streaming(behaviour):
        def wrapped(request_or_iterator, context):
            prepare(context)
            for response in behaviour(request_or_iterator, context):
                _local.request_id = request_id
                yield response

        return wrapped

    kinds = {
        (False, False): (grpc.unary_unary_rpc_method_handler, handler.unary_unary, unary),
        (False, True): (grpc.unary_stream_rpc_method_handler, handler.unary_stream, streaming),
        (True, False): (grpc.stream_unary_rpc_method_handler, handler.stream_unary, unary),
        (True, True): (grpc.stream_stream_rpc_method_handler, handler.stream_stream, streaming),
    }
    make, behaviour, wrap = kinds[(handler.request_streaming, handler.response_streaming)]
    return make(
        wrap(behaviour),
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )
