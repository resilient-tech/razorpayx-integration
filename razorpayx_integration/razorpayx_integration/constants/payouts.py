from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class RAZORPAYX_CONTACT_TYPE(BaseEnum):
    EMPLOYEE = "employee"
    SUPPLIER = "vendor"
    CUSTOMER = "customer"


class RAZORPAYX_FUND_ACCOUNT_TYPE(BaseEnum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


class RAZORPAYX_PAYOUT_MODE(BaseEnum):
    BANK = "NEFT/RTGS"  # NEFT/RTGS will be decided based on the amount at payout time
    UPI = "UPI"
    LINK = "Link"


class RAZORPAYX_PAYOUT_PURPOSE(BaseEnum):
    CUSTOMER = "refund"
    EMPLOYEE = "salary"
    SUPPLIER = "vendor_bill"


class RAZORPAYX_PAYOUT_STATUS(BaseEnum):
    NOT_INITIATED = "Not Initiated"  # custom
    QUEUED = "Queued"
    PENDING = "Pending"  # if RazorpayX workflow is enabled
    REJECTED = "Rejected"  # if RazorpayX workflow is enabled
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    CANCELLED = "Cancelled"
    REVERSED = "Reversed"
    FAILED = "Failed"
