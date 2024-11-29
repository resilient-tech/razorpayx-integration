STANDARD_FIELDS_TO_HIDE = {
    "Bank Transaction": ["transaction_id"],
    "Employee": ["bank_name", "bank_ac_no", "iban"],
}

PROPERTY_SETTERS = [
    {
        "doctype": "Bank Account",
        "fieldname": "disabled",
        "property": "default",
        "property_type": "Data",
        "value": 1,
    },
    {
        "doctype": "Bank Account",
        "fieldname": "disabled",
        "property": "depends_on",
        "property_type": "Data",
        "value": "eval: !doc.__islocal",
    },
]

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
