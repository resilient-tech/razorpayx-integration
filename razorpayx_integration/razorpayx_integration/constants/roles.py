from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    DEFAULT_PERM_LEVELS as PAYMENT_PERM_LEVELS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_PROFILES,
)
from razorpayx_integration.razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE,
)


class ROLE_PROFILES(BaseEnum):
    BANK_ACC_MANAGER = "Bank Account Manager"
    BANK_ACC_USER = "Bank Account User"


class DEFAULT_PERM_LEVELS(BaseEnum):
    BANK_ACC_MANAGER = 7
    BANK_ACC_USER = 0


ROLES = [
    # RazorpayX integration related roles
    {
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
        "role_name": PAYMENT_PROFILES.PAYMENT_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.BANK_ACC_MANAGER.value,
        "permlevel": DEFAULT_PERM_LEVELS.BANK_ACC_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES.BANK_ACC_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Payment Entry",
        "role_name": PAYMENT_PROFILES.PAYMENT_MANAGER.value,
        "permlevel": PAYMENT_PERM_LEVELS.PAYMENT_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
]

CUSTOM_PERMISSIONS = [
    {
        "module": "razorpayx_integration",
        "dt": "doctype",
        "dn": "razorpayx_integration_setting",
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
    }
]
