from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
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
    __slots__ = ("decision", "reason", "risk_score")
    DECISION_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    decision: Decision
    reason: str
    risk_score: int
    def __init__(self, decision: _Optional[_Union[Decision, str]] = ..., reason: _Optional[str] = ..., risk_score: _Optional[int] = ...) -> None: ...
