from razorpayx_integration.payment_utils.constants import SETTING_DOCTYPE

PERMISSIONS = {
    "Manager": ["select", "read", "create", "write", "delete", "email"],
    "User": ["select", "read", "create", "write"],
    "Basic": ["select", "read"],
}

ROLE_PROFILES = {
    "Payment Manger": {
        "role_name": "Payment Manager",
        "permlevel": 0,  # default
    }
}


# to make code readable
def get_role_name(profile_name: str) -> str:
    return ROLE_PROFILES[profile_name]["role_name"]


def get_permlevel(profile_name: str) -> int:
    return ROLE_PROFILES[profile_name]["permlevel"]


ROLES = [
    {
        "doctype": SETTING_DOCTYPE,
        "role_name": get_role_name("Payment Manger"),
        "permlevel": get_permlevel("Payment Manger"),
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": get_role_name("Payment Manger"),
        "permlevel": get_permlevel("Payment Manger"),
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Email Template",
        "role_name": get_role_name("Payment Manger"),
        "permlevel": get_permlevel("Payment Manger"),
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
