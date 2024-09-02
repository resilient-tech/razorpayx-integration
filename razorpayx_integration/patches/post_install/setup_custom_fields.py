from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "allow_in_quick_entry": 1,
            "in_preview": 1,
            "insert_after": "currency",
        },
    ],
    "Bank Account": [
        {
            "fieldname": "ifsc_code",
            "label": "IFSC Code",
            "fieldtype": "Data",
            "reqd": 1,
            "insert_after": "iban",
            "length": 11,
        }
    ],
}


def execute():
    create_custom_fields(CUSTOM_FIELDS)
