from razorpayx_integration.payment_utils.constants.enums import BaseEnum

# TODO: ? can remove prefix `RAZORPAYX_` from all constants
# TODO: ? what if there are custom purpose? No need for validation of purpose?? Or create doctype for purpose?


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


class RAZORPAYX_PAYOUT_LINK_STATUS(BaseEnum):
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


PAYOUT_ORDERS = {
    RAZORPAYX_PAYOUT_STATUS.NOT_INITIATED.value: 1,  # custom
    RAZORPAYX_PAYOUT_STATUS.PENDING.value: 2,
    RAZORPAYX_PAYOUT_STATUS.QUEUED.value: 3,
    RAZORPAYX_PAYOUT_STATUS.PROCESSING.value: 4,
    RAZORPAYX_PAYOUT_STATUS.PROCESSED.value: 5,
    RAZORPAYX_PAYOUT_STATUS.CANCELLED.value: 5,
    RAZORPAYX_PAYOUT_STATUS.FAILED.value: 5,
    RAZORPAYX_PAYOUT_STATUS.REJECTED.value: 5,
    RAZORPAYX_PAYOUT_STATUS.REVERSED.value: 6,
}


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
