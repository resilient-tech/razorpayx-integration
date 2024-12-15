import frappe

# API: https://violet-crews-talk.loca.lt/api/method/razorpayx_integration.razorpayx_integration.utils.webhooks.process_webhook
# regenerate code: lt --port 8001 --subdomain violet-crews-talk


@frappe.whitelist(allow_guest=True)
def process_webhook():
    """
    Process RazorpayX Webhook.
    """
    print("Webhook Received")

    form_dict = frappe.local.form_dict
    payload = frappe.request.get_data()

    print("Form Dict: ", form_dict)
    print("Payload: ", payload)
    print("Frappe Request:", frappe.request)
    print("frappe.request.data: ", frappe.request.data)
