"""
Custom fields which are helpful for payments via RazorPayX

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

from razorpayx_integration.constants import RAZORPAYX_INTEGRATION_DOCTYPE
from razorpayx_integration.payment_utils.constants.roles import PERMISSION_LEVEL
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)

CUSTOM_FIELDS = {
    "Payment Entry": [
        #### PAYMENT SECTION START ####
        {
            "fieldname": "razorpayx_payment_section",
            "label": "RazorPayX Payment Details",
            "fieldtype": "Section Break",
            "insert_after": "make_online_payment",  ## Insert After `Make Online Payment` field (Payment Utils Custom Field)
            "depends_on": "eval: doc.make_online_payment",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_account",
            "label": "RazorPayX Integration Account",
            "fieldtype": "Link",
            "insert_after": "razorpayx_payment_section",
            "options": RAZORPAYX_INTEGRATION_DOCTYPE,
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payment_mode",
            "label": "RazorPayX Payment Mode",
            "fieldtype": "Data",
            "insert_after": "razorpayx_account",
            "fetch_from": "party_bank_account.online_payment_mode",
            "depends_on": "eval: doc.razorpayx_account && doc.party_bank_account",
            "mandatory_depends_on": "eval:doc.make_online_payment && doc.razorpayx_account && doc.party_bank_account",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "read_only": 1,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_pay_instantaneously",
            "label": "Pay Instantaneously",
            "fieldtype": "Check",
            "insert_after": "razorpayx_payment_mode",
            "depends_on": f"eval: doc.razorpayx_account && doc.razorpayx_payment_mode === '{USER_PAYOUT_MODE.BANK.value}'",
            "description": "Payment will be done with <strong>IMPS</strong> mode.",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payment_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_pay_instantaneously",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payment_desc",
            "label": "Payment Description",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payment_cb",
            "depends_on": "eval: doc.razorpayx_account",
            "mandatory_depends_on": f"eval:doc.make_online_payment && doc.razorpayx_account && doc.razorpayx_payment_mode === '{USER_PAYOUT_MODE.LINK.value}'",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payment_status",
            "label": "RazorPayX Payment Status",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payment_desc",
            "options": PAYOUT_STATUS.title_case_values(as_string=True),
            "default": PAYOUT_STATUS.NOT_INITIATED.value.title(),
            "depends_on": "eval: doc.razorpayx_account && doc.creation",
            "read_only": 1,
            "allow_on_submit": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_id_sec",
            "fieldtype": "Section Break",
            "insert_after": "razorpayx_payment_status",
            "hidden": 1,
        },
        {
            "fieldname": "razorpayx_payout_id",
            "label": "RazorPayX Payout ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_id_sec",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_link_id",
            "label": "RazorPayX Payout Link ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_id",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        #### PAYMENT SECTION END ####
    ],
}
