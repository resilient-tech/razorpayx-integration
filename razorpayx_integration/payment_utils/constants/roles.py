from razorpayx_integration.payment_utils.constants import SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class ROLE_PROFILES(BaseEnum):
    AUTO_PAYMENTS_MANAGER = "Auto Payments Manager"


class DEFAULT_PERM_LEVELS(BaseEnum):
    AUTO_PAYMENTS_MANAGER = 7


PERMISSIONS = {
    "Manager": ["select", "read", "create", "write", "delete", "email"],
    "User": ["select", "read", "create", "write"],
    "Basic": ["select", "read"],
}


ROLES = [
    {
        "doctype": SETTING_DOCTYPE,
        "role_name": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Email Template",
        "role_name": ROLE_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
]
