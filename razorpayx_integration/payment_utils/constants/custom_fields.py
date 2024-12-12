"""
Custom fields which are common for making/handling payments

Note:
    - Keep sequence like this:
        1. fieldname
        2. label
        3. fieldtype
        4. insert_after
        ...
"""

# TODO: permission level are left to add

BLOCK_AUTO_PAYMENT = {
    "fieldname": "block_auto_payment",
    "label": "Block Auto Payment",
    "fieldtype": "Check",
    "description": "Auto payment will be blocked for this party",
}


CUSTOM_FIELDS = {
    "Bank Transaction": [
        {
            "fieldname": "closing_balance",
            "label": "Closing Balance",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "insert_after": "currency",
            "read_only": 1,
            "description": "As per the transaction response",
        },
    ],
    "Customer": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "payment_terms"},
    ],
    "Supplier": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "payment_terms"},
    ],
    "Employee": [
        {**BLOCK_AUTO_PAYMENT, "insert_after": "bank_name"},
    ],
}
