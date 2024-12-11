from razorpayx_integration.payment_utils.constants import SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class ROLE_PROFILES(BaseEnum):
    PAYMENT_MANAGER = "Auto Payment Manager"


class DEFAULT_PERM_LEVELS(BaseEnum):
    PAYMENT_MANAGER = 7


PERMISSIONS = {
    "Manager": ["select", "read", "create", "write", "delete", "email"],
    "User": ["select", "read", "create", "write"],
    "Basic": ["select", "read"],
}


ROLES = [
    {
        "doctype": SETTING_DOCTYPE,
        "role_name": ROLE_PROFILES.PAYMENT_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.PAYMENT_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Email Template",
        "role_name": ROLE_PROFILES.PAYMENT_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
]
