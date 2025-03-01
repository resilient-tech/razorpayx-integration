from functools import partial

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from frappe.test_runner import make_test_objects
from frappe.utils import getdate


def before_tests():
    frappe.clear_cache()

    if not frappe.db.a_row_exists("Company"):
        year = getdate().year

        setup_complete(
            {
                "currency": "INR",
                "full_name": "Test User",
                "company_name": "Acme Corporation",
                "timezone": "Asia/Kolkata",
                "company_abbr": "AC",
                "country": "India",
                "fy_start_date": f"{year}-01-01",
                "fy_end_date": f"{year}-12-31",
                "language": "English",
                "company_tagline": "Testing",
                "email": "test@example.com",
                "password": "test",
                "chart_of_accounts": "Standard",
            }
        )

    create_test_records()
    set_default_company_for_tests()
    create_rpx_config()
    # create_payment_entries()

    frappe.db.commit()  # nosemgrep

    frappe.flags.skip_test_records = True
    frappe.enqueue = partial(frappe.enqueue, now=True)


def create_test_records():
    test_records = frappe.get_file_json(
        frappe.get_app_path("razorpayx_integration", "tests", "test_records.json")
    )

    for doctype, data in test_records.items():
        make_test_objects(doctype, data, commit=True)


def set_default_company_for_tests():
    global_defaults = frappe.get_single("Global Defaults")
    global_defaults.default_company = "Globex Industries"
    global_defaults.save()


def create_rpx_config():
    doc = frappe.new_doc("RazorpayX Configuration")
    doc.update(
        {
            "key_id": "rzp_test_key_id",
            "key_secret": "rzp_test_key_secret",
            "webhook_secret": "razopayx@webhook",
            "account_id": "565632desh",
            "bank_account": "RPX - RBL",
            "account_number": "2323230070611684",
            "company": "Globex Industries",
        }
    )

    doc.insert(ignore_permissions=True, ignore_links=True)


def create_payment_entries():
    test_records = frappe.get_file_json(
        frappe.get_app_path("razorpayx_integration", "tests", "test_pe_records.json")
    )

    defaults = {
        "company": "Globex Industries",
        "bank_account": "RPX - RBL",
        "paid_from": "Bank Accounts - GI",
        "paid_to": "Creditors - GI",
    }

    for data in test_records:
        data.update(defaults)

        doc = frappe.new_doc("Payment Entry")
        doc.update(data)

        doc.setup_party_account_field()
        doc.set_missing_values()
        doc.set_exchange_rate()
        doc.received_amount = doc.paid_amount / doc.target_exchange_rate

        doc.save()
