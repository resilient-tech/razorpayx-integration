import frappe


@frappe.whitelist(allow_guest=True, methods=["POST"])
def process_webhook():
    """
    Process RazorpayX Webhook.
    """
    return "Data"
