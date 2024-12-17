from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class WEBHOOK_EVENTS_TYPE(BaseEnum):
    PAYOUT = "payout"
    PAYOUT_LINK = "payout_link"
    # TRANSACTION = "transaction" # ! NOTE: currently not supported
    # ACCOUNT = "fund_account.validation" # ! NOTE: currently not supported


# ! NOTE: currently not supported
# class WEBHOOK_FUND_ACCOUNT_EVENT(BaseEnum):
# COMPLETED = "fund_account.validation.completed"
# FAILED = "fund_account.validation.failed"


class WEBHOOK_PAYOUT_EVENT(BaseEnum):
    PENDING = "payout.pending"
    REJECTED = "payout.rejected"
    QUEUED = "payout.queued"
    INITIATED = "payout.initiated"
    PROCESSED = "payout.processed"
    UPDATED = "payout.updated"
    REVERSED = "payout.reversed"
    FAILED = "payout.failed"
    # DOWNTIME_STARTED = "payout.downtime.started"  # ! NOTE: currently not supported
    # DOWNTIME_RESOLVED = "payout.downtime.resolved" # ! NOTE: currently not supported


class WEBHOOK_PAYOUT_LINK_EVENT(BaseEnum):
    PENDING = "payout_link.pending"
    ISSUED = "payout_link.issued"
    PROCESSING = "payout_link.processing"
    PROCESSED = "payout_link.processed"
    ATTEMPTED = "payout_link.attempted"
    CANCELLED = "payout_link.cancelled"
    REJECTED = "payout_link.rejected"
    EXPIRED = "payout_link.expired"


# ! NOTE: currently not supported
# class WEBHOOK_TRANSACTION_EVENT(BaseEnum):
#     CREATED = "transaction.created"
