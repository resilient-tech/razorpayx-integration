from payment_integration_utils.payment_integration_utils.setup import (
    delete_custom_fields,
)

FIELDS_TO_DELETE = {
    "Payment Entry": ["razorpayx_payout_mode", "razorpayx_pay_instantaneously"],
    "Bank Account": [
        "online_payment_section",
        "online_payment_mode",
        "online_payment_cb",
    ],
}


def execute():
    delete_custom_fields(FIELDS_TO_DELETE)
