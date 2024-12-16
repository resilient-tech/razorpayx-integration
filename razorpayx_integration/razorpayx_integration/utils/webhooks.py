import json
from hmac import new as hmac

import frappe
from frappe import _

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    WEBHOOK_EVENTS_TYPE,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)

# API: https://sixty-bobcats-push.loca.lt/api/method/razorpayx_integration.razorpayx_integration.utils.webhooks.process_webhook
# regenerate code: lt --port 8001 --subdomain sixty-bobcats-push


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

        self.set_payload_data_to_object()

        self.verify_webhook_signature()

        self.log_razorpayx_webhook_request()

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
                "integration_request_service": "Online Banking Payment with RazorpayX",
                "request_headers": str(frappe.request.headers),
                "data": json.dumps(self.payload, indent=4),
                "status": "Queued",
                "reference_doctype": self.source_doctype,
                "reference_docname": self.source_docname,
            }
        )

        integration_request.flags.ignore_permissions = True
        integration_request.save()

        self.integration_request = integration_request

        return integration_request.name

    #### UTILITIES ####
    def set_payload_data_to_object(self):
        frappe.set_user("Administrator")

        event_type = self.payload["contains"][0]
        account_key = "razorpayx_integration_account"

        self.request_id = frappe.get_request_header("Request-Id")
        self.event = self.payload["event"]
        self.entity = self.payload["payload"][event_type]["entity"]
        self.row_payload = frappe.request.data
        self.payload = json.loads(self.row_payload)

        match event_type:
            case WEBHOOK_EVENTS_TYPE.PAYOUT.value:
                self.notes = self.entity["notes"]
            case WEBHOOK_EVENTS_TYPE.PAYOUT_LINK.value:
                self.notes = self.entity["notes"]
            case WEBHOOK_EVENTS_TYPE.TRANSACTION.value:
                self.notes = self.entity["source"]["notes"]

        self.source_doctype = self.notes["source_doctype"]
        self.source_docname = self.notes["source_docname"]

        self.razorpayx_account: RazorPayXIntegrationSetting = frappe.get_doc(
            RAZORPAYX_INTEGRATION_DOCTYPE, self.notes[account_key]
        )


@frappe.whitelist(allow_guest=True)
def process_webhook():
    """
    Process RazorpayX Webhook.
    """

    # TODO: enqueue the process_webhook function
    RazorPayXWebhook().process_webhook()


# TODO: add doc for `notes` mandatory keys in the payload : `source_doctype`, `source_docname`, `razorpayx_integration_account`
