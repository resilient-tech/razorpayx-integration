from razorpayx_integration.constants import RAZORPAYX_SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_PROFILES,
)

PAYMENT_PERM_LEVEL = 7


class ROLE_PROFILES(BaseEnum):
    BANK_ACC_MANAGER = "Bank Account Manager"
    BANK_ACC_USER = "Bank Account User"


ROLES = [
    # RazorpayX integration related roles
    {
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
        "role_name": PAYMENT_PROFILES.Auto_Payment_Manager.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.BANK_ACC_MANAGER.value,
        "permlevel": 7,
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
        "role_name": PAYMENT_PROFILES.Auto_Payment_Manager.value,
        "permlevel": PAYMENT_PERM_LEVEL,
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
