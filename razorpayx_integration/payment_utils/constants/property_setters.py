PROPERTY_SETTERS = [
    ### Payment Entry ###
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
        "doctype": "Bank Account",
        "doctype_or_docfield": "DocType",
        "property": "search_fields",
        "property_type": "Data",
        "value": "online_payment_mode,bank,account",  # TODO: not working !!
    },
]
