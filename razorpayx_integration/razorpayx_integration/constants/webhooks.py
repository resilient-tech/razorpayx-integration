from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class EVENTS_TYPE(BaseEnum):
    PAYOUT = "payout"
    PAYOUT_LINK = "payout_link"
    TRANSACTION = "transaction"
    ACCOUNT = "fund_account"  # ! NOTE: currently not supported


class FUND_ACCOUNT_EVENT(BaseEnum):
    """
    Reference: https://razorpay.com/docs/webhooks/payloads/x/account-validation/
    """

    COMPLETED = "fund_account.validation.completed"  # ! NOTE: currently not supported
    FAILED = "fund_account.validation.failed"  # ! NOTE: currently not supported


class PAYOUT_EVENT(BaseEnum):
    """
    References:
    - https://razorpay.com/docs/webhooks/payloads/x/payouts/
    - https://razorpay.com/docs/webhooks/payloads/x/payouts-approval/
    """

    PENDING = "payout.pending"
    REJECTED = "payout.rejected"
    QUEUED = "payout.queued"
    INITIATED = "payout.initiated"
    PROCESSED = "payout.processed"
    REVERSED = "payout.reversed"
    FAILED = "payout.failed"
    UPDATED = "payout.updated"
    DOWNTIME_STARTED = "payout.downtime.started"  # ! NOTE: currently not supported
    DOWNTIME_RESOLVED = "payout.downtime.resolved"  # ! NOTE: currently not supported


class PAYOUT_LINK_EVENT(BaseEnum):
    """
    Reference: https://razorpay.com/docs/webhooks/payloads/x/payout-links/
    """

    PENDING = "payout_link.pending"
    ISSUED = "payout_link.issued"
    PROCESSING = "payout_link.processing"
    PROCESSED = "payout_link.processed"
    ATTEMPTED = "payout_link.attempted"
    CANCELLED = "payout_link.cancelled"
    REJECTED = "payout_link.rejected"
    EXPIRED = "payout_link.expired"


class TRANSACTION_EVENT(BaseEnum):
    """
    Reference: https://razorpay.com/docs/webhooks/payloads/x/transactions/
    """

    CREATED = "transaction.created"


SUPPORTED_EVENTS = (
    ## PAYOUT ##
    PAYOUT_EVENT.PENDING.value,
    PAYOUT_EVENT.REJECTED.value,
    PAYOUT_EVENT.QUEUED.value,
    PAYOUT_EVENT.INITIATED.value,
    PAYOUT_EVENT.PROCESSED.value,
    PAYOUT_EVENT.REVERSED.value,
    PAYOUT_EVENT.FAILED.value,
    PAYOUT_EVENT.UPDATED.value,
    ## PAYOUT LINK ##
    PAYOUT_LINK_EVENT.PENDING.value,
    PAYOUT_LINK_EVENT.ISSUED.value,
    PAYOUT_LINK_EVENT.PROCESSING.value,
    PAYOUT_LINK_EVENT.PROCESSED.value,
    PAYOUT_LINK_EVENT.ATTEMPTED.value,
    PAYOUT_LINK_EVENT.CANCELLED.value,
    PAYOUT_LINK_EVENT.REJECTED.value,
    PAYOUT_LINK_EVENT.EXPIRED.value,
    ## TRANSACTION ##
    TRANSACTION_EVENT.CREATED.value,
)

# TODO: How to create Payment Entry without its data?
# TODO: How to handle transaction Events?
# TODO: When payout done in RazorPayX, how to create Payment Entry in ERPNext?
# TODO: Transaction even require ???
# TODO: in settings, there should checkbox for enable/disable accepting webhook which is done from RazorPayX Dashboard
# TODO: if Payout/Payout link is created from RazorPayX Dashboard, how to create Payment Entry in ERPNext?
# TODO: How to get Balance of `RazorPayX` account?
