from razorpayx_integration.payment_utils.constants.enums import BaseEnum

### REGEX ###
DESCRIPTION_REGEX = r"^[a-zA-Z0-9 ]{1,30}$"


### ENUMS ###
class CONTACT_TYPE(BaseEnum):
    EMPLOYEE = "employee"
    SUPPLIER = "vendor"
    CUSTOMER = "customer"
    SELF = "self"


class FUND_ACCOUNT_TYPE(BaseEnum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"
    # CARD = "card" # ! Not supported currently


class USER_PAYOUT_MODE(BaseEnum):
    BANK = "NEFT/RTGS"  # NEFT/RTGS will be decided based on the amount at payout time
    UPI = "UPI"
    LINK = "Link"


class PAYOUT_MODE(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "LINK"  # Actually not available in RazorpayX API
    CARD = "card"


class PAYOUT_CURRENCY(BaseEnum):
    INR = "INR"


class PAYOUT_PURPOSE(BaseEnum):
    REFUND = "refund"
    CASH_BACK = "cashback"
    PAYOUT = "payout"
    SALARY = "salary"
    UTILITY_BILL = "utility bill"
    VENDOR_BILL = "vendor bill"


class PAYOUT_STATUS(BaseEnum):
    """
    Reference:
    - https://razorpay.com/docs/x/payouts/states-life-cycle/#payout-states
    """

    # Custom Status
    NOT_INITIATED = "not initiated"

    # Payout Status
    PENDING = "pending"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"
    REVERSED = "reversed"


class PAYOUT_LINK_STATUS(BaseEnum):
    """
    Reference:
    - https://razorpay.com/docs/x/payout-links/life-cycle/
    """

    PENDING = "pending"
    ISSUED = "issued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PAYMENT_MODE_THRESHOLD(BaseEnum):
    UPI = 1_00_000  # 1 Lakh INR
    NEFT = 2_00_000  # 2 Lakh INR
    IMPS = 5_00_000  # 5 Lakh INR
    RTGS = "INFINITE"  # No Limit


### MAPPINGS ###
PAYOUT_ORDERS = {
    PAYOUT_STATUS.NOT_INITIATED.value: 1,  # custom
    PAYOUT_STATUS.PENDING.value: 2,
    PAYOUT_STATUS.QUEUED.value: 3,
    PAYOUT_STATUS.PROCESSING.value: 4,
    PAYOUT_STATUS.PROCESSED.value: 5,
    PAYOUT_STATUS.CANCELLED.value: 5,
    PAYOUT_STATUS.FAILED.value: 5,
    PAYOUT_STATUS.REJECTED.value: 5,
    PAYOUT_STATUS.REVERSED.value: 6,
}

PAYOUT_PURPOSE_MAP = {
    "Supplier": PAYOUT_PURPOSE.VENDOR_BILL.value,
    "Customer": PAYOUT_PURPOSE.UTILITY_BILL.value,
    "Employee": PAYOUT_PURPOSE.SALARY.value,
}

CONTACT_TYPE_MAP = {
    "Supplier": CONTACT_TYPE.SUPPLIER.value,
    "Customer": CONTACT_TYPE.CUSTOMER.value,
    "Employee": CONTACT_TYPE.EMPLOYEE.value,
}
