import json
from hmac import new as hmac

import frappe
from frappe import _

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    EVENTS_TYPE,
    PAYOUT_EVENT,
    PAYOUT_LINK_EVENT,
    TRANSACTION_EVENT,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)
from razorpayx_integration.razorpayx_integration.utils import (
    log_razorpayx_integration_request,
)

# API: TUNNEL_URL/api/method/razorpayx_integration.razorpayx_integration.utils.webhooks.razorpayx_webhook_listener
# regenerate code: lt --port 8001
# FIX OTP: 754081

# TODO: When to create a `Bank Transaction`
# TODO: when to cancel PE ?

# ! IMPORTANT
# TODO: only payout webhook is supported


###### WEBHOOK PROCESSORS ######
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
            PAYOUT_STATUS.REJECTED.value,
            PAYOUT_STATUS.FAILED.value,
            PAYOUT_STATUS.REVERSED.value,
            PAYOUT_STATUS.EXPIRED.value,
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


class PayoutWebhook(RazorPayXWebhook):
    pass


class PayoutLinkWebhook(RazorPayXWebhook):
    pass


class TransactionWebhook(RazorPayXWebhook):
    pass


class AccountWebhook(RazorPayXWebhook):
    pass


###### CONSTANTS ######
WEBHOOK_EVENT_TYPES_MAPPER = {
    EVENTS_TYPE.PAYOUT.value: PayoutWebhook,
    EVENTS_TYPE.PAYOUT_LINK.value: PayoutLinkWebhook,
    EVENTS_TYPE.TRANSACTION.value: TransactionWebhook,
}


###### APIs ######
@frappe.whitelist(allow_guest=True)
def razorpayx_webhook_listener():
    """
    RazorpayX Webhook Listener.
    """
    # TODO: Enqueue the webhook processing
    process_razorpayx_webhook()


def process_razorpayx_webhook():
    """
    Process RazorpayX Webhook.
    """

    def is_valid_webhook_event(event: str | None) -> bool:
        """
        Webhook event is supported or not.
        """
        if not event:
            return False

        return (
            PAYOUT_EVENT.has_value(event)
            or PAYOUT_LINK_EVENT.has_value(event)
            or TRANSACTION_EVENT.has_value(event)
        )

    event = frappe.form_dict.get("event")

    if not is_valid_webhook_event(event):
        log_razorpayx_integration_request(
            integration_request_service=f"RazorpayX Webhook Event - {event}",
            request_id=frappe.get_request_header("Request-Id"),
            request_headers=str(frappe.request.headers),
            data=frappe.form_dict,
            error="The webhook event is not supported.",
            is_remote_request=True,
        )

        return

    event_type = event.split(".")[0]

    if event_type == EVENTS_TYPE.PAYOUT.value:
        return PayoutWebhook().process_webhook()
    elif event_type == EVENTS_TYPE.PAYOUT_LINK.value:
        return PayoutLinkWebhook().process_webhook()
    elif event_type == EVENTS_TYPE.TRANSACTION.value:
        return TransactionWebhook().process_webhook()
