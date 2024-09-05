from enum import Enum

RAZORPAYX_SETTING_DOCTYPE = "RazorPayX Integration Setting"
BANK_TRANSACTION_DOCTYPE = "Bank Transaction"
RAZORPAYX = "RazorPayX"
BUG_REPORT_URL = "https://github.com/resilient-tech/razorpayx_integration/issues/new"

### Constants for APIs ###
RAZORPAYX_BASE_API_URL = "https://api.razorpay.com/v1/"
SECONDS_IN_A_DAY_MINUS_ONE = 86399  # use for to get day's end epoch time

RAZORPAYX_SUPPORTED_CURRENCY = "INR"

RAZORPAYX_SUPPORTED_HTTP_METHODS = (
    "GET",
    "DELETE",
    "POST",
    "PUT",
    "PATCH",
)


class BaseEnum(Enum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def values(cls):
        return [member.value for member in cls]


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
