from razorpayx_integration.constants.enums import BaseEnum


class RAZORPAYX_CONTACT_TYPE(BaseEnum):
    EMPLOYEE = "employee"
    SUPPLIER = "vendor"
    CUSTOMER = "customer"


class RAZORPAYX_FUND_ACCOUNT_TYPE(BaseEnum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


class RAZORPAYX_PAYOUT_MODE(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    UPI = "UPI"


class RAZORPAYX_PAYOUT_PURPOSE(BaseEnum):
    CUSTOMER = "refund"
    EMPLOYEE = "salary"
    SUPPLIER = "vendor_bill"


class RAZORPAYX_PAYOUT_STATUS(BaseEnum):
    NOT_INITIATED = "not_initiated"  # custom
    QUEUED = "queued"
    PENDING = "pending"  # if RazorpayX workflow is enabled
    REJECTED = "rejected"  # if RazorpayX workflow is enabled
    PROCESSING = "processing"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    FAILED = "failed"
