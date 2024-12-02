app_name = "razorpayx_integration"
app_title = "RazorpayX Integration"
app_publisher = "Resilient Tech"
app_description = "Automat Payments By RazorPayX API For Frappe Apps"
app_email = "info@resilient.tech"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

after_install = "razorpayx_integration.install.after_install"
before_uninstall = "razorpayx_integration.uninstall.before_uninstall"

app_include_js = "razorpayx_integration.bundle.js"

scheduler_events = {
    "daily": ["razorpayx_integration.scheduler_events.fetch_daily_transactions.execute"]
}

export_python_type_annotations = True

doc_events = {
    "Bank Account": {
        "validate": "razorpayx_integration.razorpayx_integration.server_overrides.bank_account.validate"
    }
}
