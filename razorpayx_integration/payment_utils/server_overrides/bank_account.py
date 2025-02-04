from erpnext.accounts.doctype.bank_account.bank_account import BankAccount


def validate(doc: BankAccount, method=None):
    trim_fields = ["branch_code", "bank_account_no", "upi_id"]

    for field in trim_fields:
        if value := doc.get(field):
            doc.set(field, value.strip())
