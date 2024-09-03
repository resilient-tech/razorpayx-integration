from enum import Enum

RAZORPAYX_SETTING_DOCTYPE = "RazorPayX Integration Setting"
BANK_TRANSACTION_DOCTYPE = "Bank Transaction"
RAZORPAYX = "RazorPayX"
BUG_REPORT_URL = "https://github.com/resilient-tech/razorpayx_integration/issues/new"

### Constants for APIs ###
RAZORPAYX_BASE_URL = "https://api.razorpay.com/v1/"
SECONDS_IN_A_DAY_MINUS_ONE = 86399  # use for to get day's end epoch time


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
