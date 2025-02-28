from payment_integration_utils.payment_integration_utils.constants.enums import BaseEnum
from payment_integration_utils.payment_integration_utils.constants.roles import (
    PERMISSION_LEVEL,
    PERMISSIONS,
)
from payment_integration_utils.payment_integration_utils.constants.roles import (
    ROLE_PROFILE as PAYMENT_PROFILES,
)

from razorpayx_integration.constants import RAZORPAYX_CONFIG


class ROLE_PROFILE(BaseEnum):
    RAZORPAYX_MANAGER = "RazorpayX Integration Manager"


ROLES = [
    ## RazorpayX Integration Setting ##
    {
        "doctype": RAZORPAYX_CONFIG,
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevels": PERMISSION_LEVEL.ZERO.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": RAZORPAYX_CONFIG,
        "role_name": PAYMENT_PROFILES.PAYMENT_AUTHORIZER.value,
        "permlevels": PERMISSION_LEVEL.ZERO.value,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevels": PERMISSION_LEVEL.ZERO.value,
        "permissions": PERMISSIONS["Basic"],
    },
]
