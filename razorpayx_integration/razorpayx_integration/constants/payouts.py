from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class RAZORPAYX_CONTACT_TYPE(BaseEnum):
    EMPLOYEE = "employee"
    SUPPLIER = "vendor"
    CUSTOMER = "customer"
    SELF = "self"


class RAZORPAYX_FUND_ACCOUNT_TYPE(BaseEnum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


class RAZORPAYX_USER_PAYOUT_MODE(BaseEnum):
    BANK = "NEFT/RTGS"  # NEFT/RTGS will be decided based on the amount at payout time
    UPI = "UPI"
    LINK = "Link"


class RAZORPAYX_PAYOUT_MODE(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "LINK"  # Actually not available in RazorpayX API
    CARD = "card"


class RAZORPAYX_PAYOUT_CURRENCY(BaseEnum):
    INR = "INR"


class RAZORPAYX_PAYOUT_PURPOSE(BaseEnum):
    REFUND = "refund"
    CASH_BACK = "cashback"
    PAYOUT = "payout"
    SALARY = "salary"
    UTILITY_BILL = "utility bill"
    VENDOR_BILL = "vendor bill"


class RAZORPAYX_PAYOUT_STATUS(BaseEnum):
    NOT_INITIATED = "not initiated"  # custom # Actually not available in RazorpayX API
    QUEUED = "queued"
    PENDING = "pending"  # if RazorpayX workflow is enabled
    REJECTED = "rejected"  # if RazorpayX workflow is enabled
    PROCESSING = "processing"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    FAILED = "failed"
    ISSUED = "issued"  # Payout via Link
    EXPIRED = "expired"  # Payout via Link
    ATTEMPTED = "attempted"  # Payout via Link


# if not map use `RAZORPAYX_PAYOUT_PURPOSE.PAYOUT`
PAYOUT_PURPOSE_MAP = {
    "Supplier": RAZORPAYX_PAYOUT_PURPOSE.VENDOR_BILL.value,
    "Customer": RAZORPAYX_PAYOUT_PURPOSE.UTILITY_BILL.value,
    "Employee": RAZORPAYX_PAYOUT_PURPOSE.SALARY.value,
}

CONTACT_TYPE_MAP = {
    "Supplier": RAZORPAYX_CONTACT_TYPE.SUPPLIER.value,
    "Customer": RAZORPAYX_CONTACT_TYPE.CUSTOMER.value,
    "Employee": RAZORPAYX_CONTACT_TYPE.EMPLOYEE.value,
}


class PAYMENT_MODE_THRESHOLD(BaseEnum):
    UPI = 1_00_000  # 1 Lakh INR
    NEFT = 2_00_000  # 2 Lakh INR
    IMPS = 5_00_000  # 5 Lakh INR
    RTGS = "INFINITE"  # No Limit
