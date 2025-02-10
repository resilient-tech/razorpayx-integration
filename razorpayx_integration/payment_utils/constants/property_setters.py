from razorpayx_integration.payment_utils.constants.payouts import (
    BANK_PAYMENT_MODE as PAYOUT_MODE,
)

BANK_MODES = [
    PAYOUT_MODE.NEFT.value,
    PAYOUT_MODE.RTGS.value,
    PAYOUT_MODE.IMPS.value,
]

BANK_ACCOUNT_REQD_MODES = [*BANK_MODES, PAYOUT_MODE.UPI.value]

BASE = (
    "doc.make_bank_online_payment && doc.integration_doctype && doc.integration_docname"
)
UPI_MODE_CONDITION = f"{BASE} && doc.bank_payment_mode === '{PAYOUT_MODE.UPI.value}'"
LINK_MODE_CONDITION = f"{BASE} && doc.bank_payment_mode === '{PAYOUT_MODE.LINK.value}'"
BANK_MODE_CONDITION = f"{BASE} && {BANK_MODES}.includes(doc.bank_payment_mode)"
BANK_ACCOUNT_REQD_CONDITION = (
    f"{BASE} && {BANK_ACCOUNT_REQD_MODES}.includes(doc.bank_payment_mode)"
)


PROPERTY_SETTERS = [
    ### Payment Entry ###
    # general
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_date",
        "property": "default",
        "property_type": "Data",
        "value": "Today",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_date",
        "property": "no_copy",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_no",
        "property": "no_copy",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_no",
        "property": "default",
        "property_type": "Data",
        "value": "-",
    },
    # payout/payment related
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": LINK_MODE_CONDITION + " && doc.party_type !== 'Employee'",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_email",
        "property": "depends_on",
        "property_type": "Data",
        "value": "eval: doc.contact_person || doc.party_type === 'Employee'",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_ACCOUNT_REQD_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": UPI_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "depends_on",
        "property_type": "Data",
        "value": UPI_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "mandatory_depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "depends_on",
        "property_type": "Data",
        "value": BANK_MODE_CONDITION,
    },
    ### Bank Account ###
    {
        "doctype": "Bank Account",
        "fieldname": "branch_code",
        "property": "description",
        "property_type": "Data",
        "value": "For Indian bank accounts, enter the branch <strong>IFSC code</strong>",
    },
]

# PE mandatory fields on `make_bank_online_payment`
PE_MANDATORY_FIELDS_FOR_PAYMENT = ["bank_account"]

for field in PE_MANDATORY_FIELDS_FOR_PAYMENT:
    PROPERTY_SETTERS.append(
        {
            "doctype": "Payment Entry",
            "fieldname": field,
            "property": "mandatory_depends_on",
            "property_type": "Data",
            "value": "eval: doc.make_bank_online_payment",
        }
    )

STANDARD_FIELDS_TO_HIDE = {"Employee": ["bank_name", "bank_ac_no", "iban"]}

for doctype, fields in STANDARD_FIELDS_TO_HIDE.items():
    for field in fields:
        PROPERTY_SETTERS.append(
            {
                "doctype": doctype,
                "fieldname": field,
                "property": "hidden",
                "property_type": "Check",
                "value": 1,
            }
        )
