"""
Custom fields which are helpful for payments via RazorpayX

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

from payment_integration_utils.payment_integration_utils.constants.payments import (
    TRANSFER_METHOD,
)

from razorpayx_integration.constants import RAZORPAYX_CONFIG
from razorpayx_integration.razorpayx_integration.constants.payouts import PAYOUT_STATUS
from razorpayx_integration.razorpayx_integration.constants.roles import PERMISSION_LEVEL

PAYOUT_VIA_RAZORPAYX = f"doc.make_bank_online_payment && doc.integration_doctype === '{RAZORPAYX_CONFIG}' && doc.integration_docname"
PAYOUT_BASE_CONDITION = f"doc.payment_type=='Pay' && doc.party && doc.party_type && doc.paid_from_account_currency === 'INR' && {PAYOUT_VIA_RAZORPAYX}"

CUSTOM_FIELDS = {
    "Payment Entry": [
        #### PAYOUT SECTION START ####
        {
            "fieldname": "razorpayx_payout_section",
            "label": "RazorpayX Payout Details",
            "fieldtype": "Section Break",
            "insert_after": "integration_docname",  ## Insert After `Integration Docname` field (Payment Utils Custom Field)
            "depends_on": f"eval: {PAYOUT_BASE_CONDITION}",
            "collapsible": 1,
            "collapsible_depends_on": "eval: doc.docstatus === 0",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_desc",
            "label": "Payout Description",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_section",
            "depends_on": "eval: doc.make_bank_online_payment",
            "mandatory_depends_on": f"eval: {PAYOUT_VIA_RAZORPAYX} && doc.payment_transfer_method === '{TRANSFER_METHOD.LINK.value}'",
            "length": 30,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_payout_desc",
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
        },
        {
            "fieldname": "razorpayx_payout_status",
            "label": "RazorpayX Payout Status",
            "fieldtype": "Select",
            "insert_after": "razorpayx_payout_cb",
            "options": PAYOUT_STATUS.title_case_values(as_string=True),
            "default": PAYOUT_STATUS.NOT_INITIATED.value.title(),
            "depends_on": f"eval: {PAYOUT_VIA_RAZORPAYX} && doc.creation",
            "read_only": 1,
            "allow_on_submit": 1,
            "in_list_view": 0,  # TODO: remove after split
            "in_standard_filter": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_payout_id_sec",
            "label": "RazorpayX Payout ID Section",
            "fieldtype": "Section Break",
            "insert_after": "razorpayx_payout_status",
            "hidden": 1,
        },
        {
            "fieldname": "razorpayx_payout_id",
            "label": "RazorpayX Payout ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_payout_id_sec",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        {
            "fieldname": "razorpayx_id_cb",
            "fieldtype": "Column Break",
            "insert_after": "razorpayx_payout_id",
        },
        {
            "fieldname": "razorpayx_payout_link_id",
            "label": "RazorpayX Payout Link ID",
            "fieldtype": "Data",
            "insert_after": "razorpayx_id_cb",
            "read_only": 1,
            "hidden": 1,
            "print_hide": 1,
            "permlevel": PERMISSION_LEVEL.SEVEN.value,
            "no_copy": 1,
        },
        #### PAYMENT SECTION END ####
    ],
}

# payments_processor App fields
PROCESSOR_FIELDS = {
    RAZORPAYX_CONFIG: [
        {
            "fieldname": "pay_on_auto_submit",
            "label": "Pay on Auto Submit",
            "fieldtype": "Check",
            "insert_after": "auto_cancel_payout",
            "default": "1",
            "description": "If the Payment Entry is submitted via the Payments Processor, then the payout will be initiated automatically.",
        },
    ]
}
