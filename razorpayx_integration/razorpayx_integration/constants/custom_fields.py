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
    PAYOUT_LINK_STATUS,
    PAYOUT_STATUS,
    USER_PAYOUT_MODE,
)

CUSTOM_FIELDS = {
    "Payment Entry": [
        #### PAYOUT SECTION START ####
        {
            "fieldname": "razorpayx_payout_section",
            "label": "RazorPayX Payout Details",
            "fieldtype": "Section Break",
            "insert_after": "make_bank_online_payment",  ## Insert After `Make Online Payment` field (Payment Utils Custom Field)
            "depends_on": "eval: doc.make_bank_online_payment",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_account",
            "label": "RazorPayX Integration Account",
            "fieldtype": "Link",
            "insert_after": "razorpayx_payout_section",
            "options": RAZORPAYX_INTEGRATION_DOCTYPE,
            "print_hide": 1,
            "read_only": 1,
            "hidden": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payout_mode",
            "label": "RazorPayX Payout Mode",
            "fieldtype": "Data",
            "insert_after": "razorpayx_account",
            "fetch_from": "party_bank_account.online_payment_mode",
            "depends_on": "eval: doc.razorpayx_account && doc.party_bank_account",
            "mandatory_depends_on": "eval:doc.make_bank_online_payment && doc.razorpayx_account && doc.party_bank_account",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "read_only": 1,
        },
        {
            "fieldname": "razorpayx_pay_instantaneously",
            "label": "Pay Instantaneously",
            "fieldtype": "Check",
            "insert_after": "razorpayx_payout_mode",
            "depends_on": f"eval: doc.razorpayx_account && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.BANK.value}'",
            "description": "Payment will be done with <strong>IMPS</strong> mode.",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payout_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_pay_instantaneously",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payout_desc",
            "label": "Payout Description",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_cb",
            "depends_on": "eval: doc.razorpayx_account",
            "mandatory_depends_on": f"eval:doc.make_bank_online_payment && doc.razorpayx_account && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.LINK.value}'",
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
        },
        {
            "fieldname": "razorpayx_payout_status",
            "label": "RazorPayX Payout Status",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payout_desc",
            "options": PAYOUT_STATUS.title_case_values(as_string=True),
            "default": PAYOUT_STATUS.NOT_INITIATED.value.title(),
            "depends_on": "eval: doc.razorpayx_account && doc.creation",
            "read_only": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_link_status",
            "label": "RazorPayX Payout Link Status",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payout_status",
            "options": PAYOUT_LINK_STATUS.title_case_values(as_string=True),
            "depends_on": f"eval: doc.razorpayx_account && doc.creation && doc.razorpayx_payout_mode === '{USER_PAYOUT_MODE.LINK.value}'",
            "read_only": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_id_sec",
            "label": "RazorPayX Payout ID Section",
            "fieldtype": "Section Break",
            "insert_after": "razorpayx_payout_link_status",
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
            "fieldname": "razorpayx_id_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_payout_id",
        },
        {
            "fieldname": "razorpayx_payout_link_id",
            "label": "RazorPayX Payout Link ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_id_cb",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.AUTO_PAYMENTS_MANAGER.value,
            "no_copy": 1,
        },
        #### PAYMENT SECTION END ####
    ],
}
