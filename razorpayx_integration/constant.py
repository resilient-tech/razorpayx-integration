from enum import Enum

# todo: replace Enum with strEnum

RAZORPAYX_SETTING_DOCTYPE = "RazorPayX Integration Setting"
RAZORPAYX = "RazorPayX"

### Constants for APIs ###
BASE_URL = "https://api.razorpay.com/v1/"
SECONDS_IN_A_DAY_MINUS_ONE = 86399


VALID_HTTP_METHODS = (
    "GET",
    "DELETE",
    "POST",
    "PUT",
    "PATCH",
)

UNSAFE_HTTP_METHODS = ("POST", "PUT", "PATCH")


class RAZORPAYX_CONTACT_TYPE(Enum):
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"


class RAZORPAYX_FUND_ACCOUNT_TYPE(Enum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


RAZORPAYX_CONTACT_MAP = {
    RAZORPAYX_CONTACT_TYPE.EMPLOYEE.value: "employee",
    RAZORPAYX_CONTACT_TYPE.SUPPLIER.value: "vendor",
}

AUTHORIZED_CONTACT_TYPE = [
    RAZORPAYX_CONTACT_TYPE.EMPLOYEE.value,
    RAZORPAYX_CONTACT_TYPE.SUPPLIER.value,
]

AUTHORIZED_FUND_ACCOUNT_TYPE = [
    RAZORPAYX_FUND_ACCOUNT_TYPE.BANK_ACCOUNT.value,
    RAZORPAYX_FUND_ACCOUNT_TYPE.VPA.value,
]

# * used also in Client Side, if you change below constants make changes in constant.js
SYNC_SUCCESS_RESPONSE = "success"
