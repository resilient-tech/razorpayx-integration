MANGER_PERMISSIONS = ["read", "create", "write", "delete"]
USER_PERMISSIONS = ["read", "create"]
RAZORPAYX_DOCTYPE = "RazorPayX Integration Setting"


ROLES = [
    {
        "doctypes": ["Bank Account"],
        "role_name": "RazorpayX Bank Account Manager",
        "permlevel": 0,
        "permissions": MANGER_PERMISSIONS,
    },
    {
        "doctypes": ["Bank Account"],
        "role_name": "RazorpayX Bank Account User",
        "permlevel": 0,
        "permissions": USER_PERMISSIONS,
    },
    {
        "doctypes": [RAZORPAYX_DOCTYPE],
        "role_name": "RazorpayX Payments Manager",
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
