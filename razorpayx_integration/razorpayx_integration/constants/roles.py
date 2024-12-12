from razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    DEFAULT_PERM_LEVELS as PAYMENT_PERM_LEVELS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_PROFILES,
)


class ROLE_PROFILES(BaseEnum):
    BANK_ACC_MANAGER = "Bank Account Manager"
    BANK_ACC_USER = "Bank Account User"
    RAZORPAYX_MANAGER = "RazorpayX Integration Manager"


class DEFAULT_PERM_LEVELS(BaseEnum):
    BANK_ACC_MANAGER = 7
    BANK_ACC_USER = 0
    RAZORPAYX_MANAGER = 0


ROLES = [
    # RazorpayX integration related roles
    {
        "doctype": RAZORPAYX_SETTING_DOCTYPE,
        "role_name": PAYMENT_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.BANK_ACC_MANAGER.value,
        "permlevel": DEFAULT_PERM_LEVELS.BANK_ACC_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.BANK_ACC_USER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank ##
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
        "doctype": "Bank",
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "role_name": PAYMENT_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": PAYMENT_PERM_LEVELS.AUTO_PAYMENTS_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    ## Email Template ##
    {
        "doctype": "Email Template",
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
]
