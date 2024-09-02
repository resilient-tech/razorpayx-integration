from enum import StrEnum

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


# ? can be remove
class RAZORPAYX_CONTACT_TYPE(StrEnum):
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"


class RAZORPAYX_FUND_ACCOUNT_TYPE(StrEnum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


# ? is it necessary or direct use vendor?
RAZORPAYX_CONTACT_MAP = {
    RAZORPAYX_CONTACT_TYPE.EMPLOYEE: "employee",
    RAZORPAYX_CONTACT_TYPE.SUPPLIER: "vendor",
}

AUTHORIZED_CONTACT_TYPE = (
    RAZORPAYX_CONTACT_TYPE.EMPLOYEE,
    RAZORPAYX_CONTACT_TYPE.SUPPLIER,
)

AUTHORIZED_FUND_ACCOUNT_TYPE = (
    RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT,
    RAZORPAYX_FUND_ACCOUNT_TYPE.VPA,
)

# * used also in Client Side, if you change below constants make changes in constant.js
SYNC_SUCCESS_RESPONSE = "success"
