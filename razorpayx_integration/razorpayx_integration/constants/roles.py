from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSION_LEVEL,
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILE as PAYMENT_PROFILES,
)

# TODO: one bank account can be used in only one integration at a time
# TODO: how can we restrict this?


class ROLE_PROFILE(BaseEnum):
    RAZORPAYX_MANAGER = "RazorPayX Integration Manager"


ROLES = [
    ## RazorPayX Integration Setting ##
    {
        "doctype": RAZORPAYX_INTEGRATION_DOCTYPE,
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevels": PERMISSION_LEVEL.ZERO.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": RAZORPAYX_INTEGRATION_DOCTYPE,
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
