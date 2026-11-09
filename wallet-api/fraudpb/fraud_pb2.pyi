from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Decision(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DECISION_UNSPECIFIED: _ClassVar[Decision]
    APPROVE: _ClassVar[Decision]
    DECLINE: _ClassVar[Decision]
DECISION_UNSPECIFIED: Decision
APPROVE: Decision
DECLINE: Decision

class CheckPaymentRequest(_message.Message):
    __slots__ = ("transaction_id", "user_id", "card_last4", "amount", "currency", "merchant_name", "merchant_category")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CARD_LAST4_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    MERCHANT_NAME_FIELD_NUMBER: _ClassVar[int]
    MERCHANT_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    user_id: str
    card_last4: str
    amount: str
    currency: str
    merchant_name: str
    merchant_category: str
    def __init__(self, transaction_id: _Optional[str] = ..., user_id: _Optional[str] = ..., card_last4: _Optional[str] = ..., amount: _Optional[str] = ..., currency: _Optional[str] = ..., merchant_name: _Optional[str] = ..., merchant_category: _Optional[str] = ...) -> None: ...

class CheckPaymentResponse(_message.Message):
    __slots__ = ("decision", "reason", "risk_score", "transaction_id")
    DECISION_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    decision: Decision
    reason: str
    risk_score: int
    transaction_id: str
    def __init__(self, decision: _Optional[_Union[Decision, str]] = ..., reason: _Optional[str] = ..., risk_score: _Optional[int] = ..., transaction_id: _Optional[str] = ...) -> None: ...

class GetDecisionRequest(_message.Message):
    __slots__ = ("transaction_id",)
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    def __init__(self, transaction_id: _Optional[str] = ...) -> None: ...

class WatchRiskEventsRequest(_message.Message):
    __slots__ = ("min_risk_score",)
    MIN_RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    min_risk_score: int
    def __init__(self, min_risk_score: _Optional[int] = ...) -> None: ...

class RiskEvent(_message.Message):
    __slots__ = ("transaction_id", "user_id", "decision", "reason", "risk_score", "amount", "currency", "occurred_at", "request_id")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    OCCURRED_AT_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    user_id: str
    decision: Decision
    reason: str
    risk_score: int
    amount: str
    currency: str
    occurred_at: str
    request_id: str
    def __init__(self, transaction_id: _Optional[str] = ..., user_id: _Optional[str] = ..., decision: _Optional[_Union[Decision, str]] = ..., reason: _Optional[str] = ..., risk_score: _Optional[int] = ..., amount: _Optional[str] = ..., currency: _Optional[str] = ..., occurred_at: _Optional[str] = ..., request_id: _Optional[str] = ...) -> None: ...

class BatchSummary(_message.Message):
    __slots__ = ("total", "approved", "declined", "declined_transaction_ids")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    APPROVED_FIELD_NUMBER: _ClassVar[int]
    DECLINED_FIELD_NUMBER: _ClassVar[int]
    DECLINED_TRANSACTION_IDS_FIELD_NUMBER: _ClassVar[int]
    total: int
    approved: int
    declined: int
    declined_transaction_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, total: _Optional[int] = ..., approved: _Optional[int] = ..., declined: _Optional[int] = ..., declined_transaction_ids: _Optional[_Iterable[str]] = ...) -> None: ...
