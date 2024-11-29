MANGER_PERMISSIONS = ["select", "read", "create", "write", "delete", "email"]
USER_PERMISSIONS = ["read", "create", "write"]
BASIC_PERMISSIONS = ["select", "read"]
RAZORPAYX_DOCTYPE = "RazorPayX Integration Setting"


ROLE_PROFILE = {
    "Bank Account Manager": "RazorpayX Bank Account Manager",
    "Bank Account User": "RazorpayX Bank Account User",
    "Payments Manager": "RazorpayX Payments Manager",
}

# todo: can be more efficient and more roles and permissions can be added
ROLES = [
    {
        "doctypes": ["Bank Account"],
        "role_name": ROLE_PROFILE["Bank Account Manager"],
        "permlevel": 0,
        "permissions": MANGER_PERMISSIONS,
    },
    {
        "doctypes": ["Bank Account"],
        "role_name": ROLE_PROFILE["Bank Account User"],
        "permlevel": 0,
        "permissions": USER_PERMISSIONS,
    },
    {
        "doctypes": ["Bank"],
        "role_name": ROLE_PROFILE["Bank Account User"],
        "permlevel": 0,
        "permissions": BASIC_PERMISSIONS,
    },
    {
        "doctypes": ["Bank"],
        "role_name": ROLE_PROFILE["Bank Account Manager"],
        "permlevel": 0,
        "permissions": BASIC_PERMISSIONS,
    },
    {
        "doctypes": [RAZORPAYX_DOCTYPE],
        "role_name": ROLE_PROFILE["Payments Manager"],
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
