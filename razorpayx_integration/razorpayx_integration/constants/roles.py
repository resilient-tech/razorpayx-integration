from payment_integration_utils.payment_integration_utils.constants.enums import BaseEnum
from payment_integration_utils.payment_integration_utils.constants.roles import (
    PERMISSION_LEVEL,
    PERMISSIONS,
)
from payment_integration_utils.payment_integration_utils.constants.roles import (
    ROLE_PROFILE as PAYMENT_PROFILES,
)

from razorpayx_integration.constants import (
    RAZORPAYX_SETTING,
)

# TODO: one bank account can be used in only one integration at a time
# TODO: how can we restrict this?


class ROLE_PROFILE(BaseEnum):
    RAZORPAYX_MANAGER = "RazorpayX Integration Manager"


ROLES = [
    ## RazorpayX Integration Setting ##
    {
        "doctype": RAZORPAYX_SETTING,
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevels": PERMISSION_LEVEL.ZERO.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": RAZORPAYX_SETTING,
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
