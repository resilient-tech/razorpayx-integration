import json
from hmac import new as hmac

import frappe
from frappe import _

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    RAZORPAYX_PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    WEBHOOK_EVENTS_TYPE,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)

# API: TUNNEL_URL/api/method/razorpayx_integration.razorpayx_integration.utils.webhooks.process_webhook
# regenerate code: lt --port 8001

# TODO: When to create a `Bank Transaction`
# TODO: when to cancel PE ?

# ! IMPORTANT
# TODO: only payout webhook is supported


class RazorPayXWebhook:
    def __init__(self):
        self.event_id = frappe.get_request_header("X-Razorpay-Event-Id")
        self.signature = frappe.get_request_header("X-Razorpay-Signature")

    def process_webhook(self):
        """
        Process RazorpayX Webhook.
        """
        if not (self.event_id and self.signature):
            return

        if frappe.cache().get_value(self.event_id):
            return

        frappe.cache().set_value(self.event_id, True, expires_in_sec=60)

        self.initialize_payload_data()

        self.verify_webhook_signature()

        self.log_razorpayx_webhook_request()

        self.update_payment_entry()

    def verify_webhook_signature(self):
        """
        Verify the signature of the payload.
        """
        webhook_secret = self.razorpayx_account.get_password("webhook_secret").encode()

        expected_signature = hmac(
            webhook_secret, self.row_payload, "sha256"
        ).hexdigest()

        if self.signature != expected_signature:
            frappe.throw(
                title="Invalid RazorpayX Webhook Signature",
                message=f"Payload: \n {self.payload}",
            )

    def log_razorpayx_webhook_request(self):
        """
        Log RazorpayX Webhook Request.
        """
        integration_request = frappe.new_doc("Integration Request")

        integration_request.update(
            {
                "request_id": self.request_id,
                "razorpayx_event_id": self.event_id,
                "razorpayx_event": self.event,
                "razorpayx_payment_status": self.payment_status.title(),
                "integration_request_service": "Online Banking Payment with RazorpayX",
                "request_headers": str(frappe.request.headers),
                "data": json.dumps(self.payload, indent=4),
                "status": "Authorized",
                "reference_doctype": self.source_doctype,
                "reference_docname": self.source_docname,
            }
        )

        integration_request.flags.ignore_permissions = True
        integration_request.save()

        self.integration_request = integration_request

        return integration_request.name

    def update_payment_entry(self):
        if self.source_doctype != "Payment Entry":
            return

        pe = frappe.get_doc("Payment Entry", self.source_docname)

        if not self.does_order_maintained(pe.razorpayx_payment_status.title()):
            return

        values = {
            "razorpayx_payment_status": self.payment_status.title(),
        }

        if self.utr:
            values["reference_no"] = self.utr

        pe.db_set(values, update_modified=True)

        if self.payment_status in [
            RAZORPAYX_PAYOUT_STATUS.REJECTED.value,
            RAZORPAYX_PAYOUT_STATUS.FAILED.value,
            RAZORPAYX_PAYOUT_STATUS.REVERSED.value,
            RAZORPAYX_PAYOUT_STATUS.EXPIRED.value,
        ]:
            pe.cancel()

    #### UTILITIES ####
    def initialize_payload_data(self):
        frappe.set_user("Administrator")
        account_key = "razorpayx_integration_account"

        self.request_id = frappe.get_request_header("Request-Id")

        self.row_payload = frappe.request.data
        self.payload = json.loads(self.row_payload)

        event_type = self.payload["contains"][0]
        self.event = self.payload["event"]
        self.payout_entity = self.payload["payload"][event_type]["entity"]

        self.payment_status = self.payout_entity["status"]
        self.utr = self.payout_entity["utr"]

        self.notes = self.payout_entity["notes"]
        self.source_doctype = self.notes["source_doctype"]
        self.source_docname = self.notes["source_docname"]

        self.razorpayx_account: RazorPayXIntegrationSetting = frappe.get_doc(
            RAZORPAYX_INTEGRATION_DOCTYPE, self.notes[account_key]
        )

    def does_order_maintained(self, pe_payment_status):
        # TODO: check if the order is maintained
        return True


@frappe.whitelist(allow_guest=True)
def process_webhook():
    """
    Process RazorpayX Webhook.
    """

    # TODO: enqueue the process_webhook function
    # RazorPayXWebhook().process_webhook()
    print("\n\n Webhook Received \n\n")

    IR = frappe.new_doc("Integration Request")

    row_payload = frappe.request.data
    payload = json.loads(row_payload)

    print("\n\n Webhook Payload \n\n")
    print(payload)

    IR.update(
        {
            "integration_request_service": "RazorpayX Webhooks",
            "request_headers": str(frappe.request.headers),
            "data": json.dumps(payload, indent=4),
            "status": "Completed",
        }
    )

    IR.flags.ignore_permissions = True

    IR.save()


# TODO: add doc for `notes` mandatory keys in the payload : `source_doctype`, `source_docname`, `razorpayx_integration_account`
