DEFAULT_REFERENCE_NO = "-*--*-"

# TODO: ? make `branch_code` and `bank_account_no` as mandatory fields if mode of payment is `Bank` ?
PROPERTY_SETTERS = [
    ### Payment Entry ###
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_no",
        "property": "default",
        "property_type": "Data",
        "value": DEFAULT_REFERENCE_NO,
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
        "fieldname": "contact_email",
        "property": "no_copy",
        "property_type": "Check",
        "value": 1,
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "contact_person",
        "property": "no_copy",
        "property_type": "Check",
        "value": 0,
    },
]
