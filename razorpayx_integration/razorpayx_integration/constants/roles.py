from razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILES as PAYMENT_PROFILES,
)


class ROLE_PROFILES(BaseEnum):
    RAZORPAYX_MANAGER = "RazorpayX Integration Manager"


class DEFAULT_PERM_LEVELS(BaseEnum):
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
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank ##
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Email Template ##
    {
        "doctype": "Email Template",
        "role_name": ROLE_PROFILES.RAZORPAYX_MANAGER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["User"],
    },
]
