from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# todo: new fields require in `Payment Entry` for `RazorPayX` integration
CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "insert_after": "currency",
        },
    ],
}


def execute():
    create_custom_fields(CUSTOM_FIELDS)
