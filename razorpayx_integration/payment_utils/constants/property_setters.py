DEFAULT_REFERENCE_NO = "-*--*-"

PROPERTY_SETTERS = [
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
        "property": "allow_on_submit",
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
        "fieldname": "reference_date",
        "property": "default",
        "property_type": "Data",
        "value": "Today",
    },
    {
        "doctype": "Payment Entry",
        "fieldname": "reference_date",
        "property": "allow_on_submit",
        "property_type": "Check",
        "value": 1,
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
]
