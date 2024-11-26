STANDARD_FIELDS_TO_HIDE = {
    "Bank Transaction": ["transaction_id"],
    "Employee": ["bank_name", "bank_ac_no", "iban"],
}

PROPERTY_SETTERS = []

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
