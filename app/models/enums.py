from enum import Enum


class AccountType(str, Enum):
    checking = "checking"
    savings = "savings"


class AccountStatus(str, Enum):
    active = "active"
    frozen = "frozen"
    closed = "closed"


class TransactionType(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"
    fee = "fee"


class TransactionStatus(str, Enum):
    posted = "posted"
    failed = "failed"


class TransferStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class CardType(str, Enum):
    debit = "debit"
    credit = "credit"


class CardStatus(str, Enum):
    active = "active"
    frozen = "frozen"
    cancelled = "cancelled"
