from razorpayx_integration.constants import RAZORPAYX_SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_PROFILE,
)

PAYMENT_PERM_LEVEL = 7

ROLE_PROFILES = {
    "Bank Acc Manager": {
        "role_name": "Bank Account Manager",
        "permlevel": 7,  # default
    },
    "Bank Acc User": {
        "role_name": "Bank Account User",
        "permlevel": 0,  # default
    },
}


ROLES = [
    # RazorpayX integration related roles
    {
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
        "role_name": PAYMENT_PROFILE["Payment Manger"]["role_name"],
        "permlevel": PAYMENT_PROFILE["Payment Manger"]["permlevel"],
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES["Bank Acc Manager"]["role_name"],
        "permlevel": ROLE_PROFILES["Bank Acc Manager"]["permlevel"],
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES["Bank Acc User"]["role_name"],
        "permlevel": ROLE_PROFILES["Bank Acc User"]["permlevel"],
        "permissions": PERMISSIONS["User"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES["Bank Acc Manager"]["role_name"],
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES["Bank Acc User"]["role_name"],
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Payment Entry",
        "role_name": PAYMENT_PROFILE["Payment Manger"]["role_name"],
        "permlevel": PAYMENT_PERM_LEVEL,
        "permissions": PERMISSIONS["Manager"],
    }
]

CUSTOM_PERMISSIONS = [
    {
        "module": "razorpayx_integration",
        "dt": "doctype",
        "dn": "razorpayx_integration_setting",
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
    }
]
