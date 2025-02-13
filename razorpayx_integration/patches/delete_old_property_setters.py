from payment_integration_utils.payment_integration_utils.utils import (
    delete_property_setters,
)

PROPERTY_SETTERS_TO_DELETE = [
    ## Payment Entry ##
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "mandatory_depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "mandatory_depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_upi_id",
        "property": "depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "mandatory_depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_account_no",
        "property": "depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "mandatory_depends_on",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "party_bank_ifsc",
        "property": "depends_on",
    },
    ## Bank Account ##
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "options",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "description",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "online_payment_mode",
        "property": "depends_on",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "bank_account_no",
        "property": "mandatory_depends_on",
    },
    {
        "doctype": "Bank Account",
        "fieldname": "branch_code",
        "property": "mandatory_depends_on",
    },
]


def execute():
    delete_property_setters(PROPERTY_SETTERS_TO_DELETE)
