from razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE as RAZORPAYX_DOCTYPE,
)
from razorpayx_integration.constants.enums import BaseEnum

MANGER_PERMISSIONS = ["select", "read", "create", "write", "delete", "email"]
USER_PERMISSIONS = ["read", "create", "write"]
BASIC_PERMISSIONS = ["select", "read"]


class ROLE_PROFILE(BaseEnum):
    BANK_ACC_MANAGER = "RazorpayX Bank Account Manager"
    BANK_ACC_USER = "RazorpayX Bank Account User"
    PAYMENTS_MANAGER = "RazorpayX Payments Manager"


# todo: can be more efficient and more roles and permissions can be added
ROLES = [
    {
        "doctypes": ["Bank Account"],
        "role_name": ROLE_PROFILE.BANK_ACC_MANAGER.value,
        "permlevel": 0,
        "permissions": MANGER_PERMISSIONS,
    },
    {
        "doctypes": ["Bank Account"],
        "role_name": ROLE_PROFILE.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": USER_PERMISSIONS,
    },
    {
        "doctypes": ["Bank"],
        "role_name": ROLE_PROFILE.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": BASIC_PERMISSIONS,
    },
    {
        "doctypes": ["Bank"],
        "role_name": ROLE_PROFILE.BANK_ACC_MANAGER.value,
        "permlevel": 0,
        "permissions": BASIC_PERMISSIONS,
    },
    {
        "doctypes": [RAZORPAYX_DOCTYPE],
        "role_name": ROLE_PROFILE.PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": MANGER_PERMISSIONS,
    },
]

CUSTOM_PERMISSIONS = [
    {
        "module": "razorpayx_integration",
        "dt": "doctype",
        "dn": "razorpayx_integration_setting",
        "doctype": RAZORPAYX_DOCTYPE,
    }
]
