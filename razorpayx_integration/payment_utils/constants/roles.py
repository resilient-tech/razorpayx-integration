from razorpayx_integration.payment_utils.constants import SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class ROLE_PROFILES(BaseEnum):
    Auto_Payment_Manager = "Auto Payment Manager"


PERMISSIONS = {
    "Manager": ["select", "read", "create", "write", "delete", "email"],
    "User": ["select", "read", "create", "write"],
    "Basic": ["select", "read"],
}


ROLES = [
    {
        "doctype": SETTING_DOCTYPE,
        "role_name": ROLE_PROFILES.Auto_Payment_Manager.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.Auto_Payment_Manager.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Email Template",
        "role_name": ROLE_PROFILES.Auto_Payment_Manager.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
]

CUSTOM_PERMISSIONS = [
    {
        "module": "payment_utils",
        "dt": "doctype",
        "dn": "payment_setting",
        "doctype": SETTING_DOCTYPE,
    }
]
