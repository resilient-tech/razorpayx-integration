from razorpayx_integration.payment_utils.constants import SETTING_DOCTYPE
from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class ROLE_PROFILE(BaseEnum):
    BANK_ACC_MANAGER = "Bank Account Manager"
    BANK_ACC_USER = "Bank Account User"
    AUTO_PAYMENTS_MANAGER = "Auto Payments Manager"


class FRAPPE_ROLE_PROFILE(BaseEnum):
    ALL = "All"
    SYSTEM_MANAGER = "System Manager"


class PERMISSION_LEVEL(BaseEnum):
    BANK_ACC_MANAGER = 7
    BANK_ACC_USER = 0
    AUTO_PAYMENTS_MANAGER = 7


PERMISSIONS = {
    "Manager": [
        "select",
        "read",
        "create",
        "write",
        "delete",
        "email",
        "submit",
        "cancel",
        "amend",
    ],
    "User": ["select", "read", "create", "write"],
    "Basic": ["select", "read"],
}


ROLES = [
    ## Setting Doctype ##
    {
        "doctype": SETTING_DOCTYPE,
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    ## Bank ##
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILE.BANK_ACC_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILE.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILE.BANK_ACC_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.BANK_ACC_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILE.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Payment Entry",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    # Customer
    {
        "doctype": "Customer",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
    # Supplier
    {
        "doctype": "Supplier",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
    # Employee
    {
        "doctype": "Employee",
        "role_name": ROLE_PROFILE.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
]
