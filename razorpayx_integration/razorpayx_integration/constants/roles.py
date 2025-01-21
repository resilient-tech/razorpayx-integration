from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.constants.roles import (
    PERMISSIONS,
)
from razorpayx_integration.payment_utils.constants.roles import (
    ROLE_PROFILE as PAYMENT_PROFILES,
)


class ROLE_PROFILE(BaseEnum):
    RAZORPAYX_MANAGER = "RazorPayX Integration Manager"
    PAYOUT_AUTHORIZER = "RazorPayX Payout Authorizer"


class PERMISSION_LEVEL(BaseEnum):
    RAZORPAYX_MANAGER = 0
    PAYOUT_AUTHORIZER = 7  # same as AUTO_PAYMENTS_MANAGER


ROLES = [
    # RazorpayX integration related roles
    {
        "doctype": RAZORPAYX_INTEGRATION_DOCTYPE,
        "role_name": PAYMENT_PROFILES.AUTO_PAYMENTS_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.RAZORPAYX_MANAGER.value,
        "permissions": PERMISSIONS["Basic"],
    },
    {
        "doctype": RAZORPAYX_INTEGRATION_DOCTYPE,
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.RAZORPAYX_MANAGER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": RAZORPAYX_INTEGRATION_DOCTYPE,
        "role_name": ROLE_PROFILE.PAYOUT_AUTHORIZER.value,
        "permlevel": PERMISSION_LEVEL.RAZORPAYX_MANAGER.value,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.RAZORPAYX_MANAGER.value,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Bank ##
    {
        "doctype": "Bank",
        "role_name": ROLE_PROFILE.RAZORPAYX_MANAGER.value,
        "permlevel": PERMISSION_LEVEL.RAZORPAYX_MANAGER.value,
        "permissions": PERMISSIONS["Basic"],
    },
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "role_name": ROLE_PROFILE.PAYOUT_AUTHORIZER.value,
        "permlevel": PERMISSION_LEVEL.PAYOUT_AUTHORIZER.value,
        "permissions": PERMISSIONS["Manager"],
    },
    {
        "doctype": "Payment Entry",
        "role_name": ROLE_PROFILE.PAYOUT_AUTHORIZER.value,
        "permlevel": 0,
        "permissions": PERMISSIONS["Manager"],
    },
]
