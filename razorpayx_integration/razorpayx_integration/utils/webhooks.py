import json
from hmac import new as hmac

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form, get_url_to_form

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.property_setters import (
    DEFAULT_REFERENCE_NO,
)
from razorpayx_integration.payment_utils.utils import log_integration_request
from razorpayx_integration.razorpayx_integration.apis.payout import RazorPayXLinkPayout
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_LINK_STATUS,
    PAYOUT_ORDERS,
    PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    EVENTS_TYPE,
    SUPPORTED_EVENTS,
)
from razorpayx_integration.razorpayx_integration.doctype.razorpayx_integration_setting.razorpayx_integration_setting import (
    RazorPayXIntegrationSetting,
)

# API: TUNNEL_URL/api/method/razorpayx_integration.razorpayx_integration.utils.webhooks.razorpayx_webhook_listener
# regenerate code: lt --port 8001
# FIX OTP: 754081

# TODO: When to create a `Bank Transaction`
# TODO: when to cancel PE ?
# TODO: TESTINGS

# ! IMPORTANT
# TODO: only payout webhook is supported


###### WEBHOOK PROCESSORS ######
class RazorPayXWebhook:
    ### SETUP ###
    def __init__(self):
        """
        Caution: ⚠️ Don't forget to call `super().__init__()` in sub class.
        """
        frappe.set_user("Administrator")

        self.event_id = frappe.get_request_header("X-Razorpay-Event-Id")
        self.signature = frappe.get_request_header("X-Razorpay-Signature")

        self.request_id = frappe.get_request_header("Request-Id")

        self.row_payload = frappe.request.data
        self.payload = json.loads(self.row_payload)

        self.initialize_payload_data()
        self.verify_webhook_signature()
        self.log_razorpayx_webhook_request()

    def initialize_payload_data(self):
        """
        Initialize the payload data to be used in the webhook processing.

        Caution: ⚠️ Don't forget to call `super().initialize_payload_data()` in sub class.
        """
        self.event = self.payload["event"]
        self.event_type = self.event.split(".")[0]

        self.entity = (
            self.payload.get("payload", {}).get(self.event_type, {}).get("entity", {})
        )

        ### Entity data related to payout or link ###
        self.status = ""
        self.utr = ""
        self.id = ""

        if self.entity:
            self.status = self.entity.get("status")
            self.utr = self.entity.get("utr")
            self.id = self.entity.get("id")

        ### Source doc data ###
        self.source_docname = ""
        self.source_doctype = ""

        self.notes = self.entity.get("notes", {})
        if self.notes and isinstance(self.notes, dict):
            self.source_doctype = self.notes.get("source_doctype", "")
            self.source_docname = self.notes.get("source_docname", "")

        ### RazorpayX account ###
        self.razorpayx_account: RazorPayXIntegrationSetting = (
            self.get_razorpayx_account()
        )

    def process_webhook(self):
        """
        Process RazorpayX Webhook.

        Note: This method should be overridden in the sub class.
        """
        pass

    ### VALIDATIONS ###
    def verify_webhook_signature(self):
        """
        Verify the signature of the payload.

        :raises: frappe.ValidationError
        """
        if not self.razorpayx_account:
            frappe.throw(
                title="RazorpayX Account Not Found",
                message=f"Payload: \n {self.payload}",
            )

        webhook_secret = self.razorpayx_account.get_password("webhook_secret").encode()

        expected_signature = hmac(
            webhook_secret, self.row_payload, "sha256"
        ).hexdigest()

        if self.signature != expected_signature:
            frappe.throw(
                title="Invalid RazorpayX Webhook Signature",
                message=f"Payload: \n {self.payload}",
            )

    #### UTILITIES ####
    def log_razorpayx_webhook_request(self):
        """
        Log RazorpayX Webhook Request.
        """
        ir = log_integration_request(
            integration_request_service=f"RazorPayX Webhook Event - {self.event}",
            request_id=self.request_id,
            request_headers=str(frappe.request.headers),
            data=self.payload,
            reference_doctype=self.source_doctype,
            reference_name=self.source_docname,
            is_remote_request=True,
        )

        self.integration_request = ir.name

    def get_razorpayx_account(
        self, account_id: str | None = None
    ) -> RazorPayXIntegrationSetting | None:
        """
        Get RazorpayX Account Doc.

        :param account_id: RazorpayX Account ID (Business ID).

        Note: `account_id` must start with `acc_`.
        """
        if not account_id:
            account_id = self.payload.get("account_id")

        if not account_id:
            return

        account_id = account_id.removeprefix("acc_")

        return frappe.get_doc(RAZORPAYX_INTEGRATION_DOCTYPE, {"account_id": account_id})

    def get_source_doc(self):
        """
        Get the source doc.
        """
        if not self.source_doctype or not self.source_docname:
            return

        return frappe.get_doc(self.source_doctype, self.source_docname)

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Note: This method should be overridden in the sub class.
        """
        pass

    def is_webhook_processable(self) -> bool:
        """
        Check if the webhook is processable or not.

        Only process the webhook if the source docname and source doctype is available.
        """
        return bool(self.source_doctype and self.source_docname)

    def get_ir_formlink(self, html: bool = False) -> str:
        """
        Get the Integration Request Form Link.

        :param html: bool - If True, return the HTML link.
        """
        if html:
            return get_link_to_form("Integration Request", self.integration_request)

        return get_url_to_form("Integration Request", self.integration_request)


class PayoutWebhook(RazorPayXWebhook):
    ### APIs ###
    def process_webhook(self):
        """
        Process RazorpayX Payout Webhook.
        """
        if not self.is_webhook_processable():
            return

        self.source_doc: PaymentEntry = self.get_source_doc()

        if not self.source_doc or not self.is_order_maintained():
            return

        self.update_payment_entry()

    ### UTILITIES ###
    def is_webhook_processable(self) -> bool:
        return bool(self.source_doctype == "Payment Entry" and self.source_docname)

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Compare webhook status with the source doc status and payment status.
        """
        pe_status = self.source_doc.razorpayx_payment_status.lower()

        if not self.status or self.source_doc.docstatus != 1:
            return False

        # If the current webhook status's order is less than or equal to the PE status, then order not maintained.
        if PAYOUT_ORDERS[self.status] <= PAYOUT_ORDERS[pe_status]:
            return False

        return True

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - Update the status of the Payment Entry.
        - Update the UTR Number.
        - If failed, cancel the Payment Entry and Payout Link.
        """
        values = {
            "razorpayx_payment_status": self.status.title(),
        }

        if self.source_doc.reference_no == DEFAULT_REFERENCE_NO and self.utr:
            values["reference_no"] = self.utr

            if self.source_doc.remarks:
                values["remarks"] = self.source_doc.remarks.replace(
                    self.source_doc.reference_no, self.utr
                )

        if self.id:
            values["razorpayx_payout_id"] = self.id

        self.source_doc.db_set(values, notify=True)

        if self.should_cancel_payment_entry() and self.cancel_payout_link():
            self.source_doc.flags.__canceled_by_rpx_webhook = True
            self.source_doc.cancel()

    def cancel_payout_link(self) -> bool:
        """
        Cancel the Payout Link.

        :returns: bool - `True` if the Payout Link is cancelled successfully.
        """
        if not self.source_doc.razorpayx_payout_link_id:
            return True

        try:
            payout_link = RazorPayXLinkPayout(self.razorpayx_account.name)
            id = self.source_doc.razorpayx_payout_link_id

            status = payout_link.get_by_id(id, "status")

            if status in [
                PAYOUT_LINK_STATUS.CANCELLED.value,
                PAYOUT_LINK_STATUS.EXPIRED.value,
                PAYOUT_LINK_STATUS.REJECTED.value,
            ]:
                return True

            if status == PAYOUT_LINK_STATUS.ISSUED.value:
                payout_link.cancel(self.source_doc.razorpayx_payout_link_id)
                return True

        except Exception:
            frappe.log_error(
                title="RazorpayX Payout Link Cancellation Failed",
                message=f"Source: {self.get_ir_formlink()} \n\n Traceback: \n {frappe.get_traceback()}",
            )

    def should_cancel_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be cancelled or not.
        """
        if not self.status or self.source_doc.docstatus == 2:
            return False

        if self.status in [
            PAYOUT_STATUS.CANCELLED.value,
            PAYOUT_STATUS.FAILED.value,
            PAYOUT_STATUS.REVERSED.value,
            PAYOUT_STATUS.REJECTED.value,
        ]:
            return True


class PayoutLinkWebhook(RazorPayXWebhook):
    ### APIs ###
    def process_webhook(self):
        """
        Process RazorpayX Payout Link Webhook.
        """
        if not self.is_webhook_processable():
            return

        self.source_doc: PaymentEntry = self.get_source_doc()

        if not self.source_doc or not self.is_order_maintained():
            return

        self.update_payment_entry()

    ### UTILITIES ###
    def is_webhook_processable(self) -> bool:
        return bool(self.source_doctype == "Payment Entry" and self.source_docname)

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Caution: ⚠️ Payout link status is not maintained in the Payment Entry.
        """
        return self.status and self.source_doc.docstatus == 1

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - Update the status of the Payment Entry.
        - Update the UTR Number.
        - If failed, cancel the Payment Entry.
        """
        values = {}

        cancel_pe = self.should_cancel_payment_entry()

        if cancel_pe:
            values["razorpayx_payment_status"] = PAYOUT_STATUS.CANCELLED.value

        if self.source_doc.reference_no == DEFAULT_REFERENCE_NO and self.utr:
            values["reference_no"] = self.utr

            if self.source_doc.remarks:
                values["remarks"] = self.source_doc.remarks.replace(
                    self.source_doc.reference_no, self.utr
                )

        if not self.source_doc.razorpayx_payout_link_id and self.id:
            values["razorpayx_payout_link_id"] = self.id

        self.source_doc.db_set(values, notify=True)

        if cancel_pe:
            self.source_doc.flags.__canceled_by_rpx_webhook = True
            self.source_doc.cancel()

    def should_cancel_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be cancelled or not.
        """
        if not self.status or self.source_doc.docstatus == 2:
            return False

        if self.status in [
            PAYOUT_LINK_STATUS.CANCELLED.value,
            PAYOUT_LINK_STATUS.EXPIRED.value,
            PAYOUT_LINK_STATUS.REJECTED.value,
        ]:
            return True


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
    # Check if the event is already processed
    event_id = frappe.get_request_header("X-Razorpay-Event-Id")
    signature = frappe.get_request_header("X-Razorpay-Signature")

    if not (event_id and signature):
        return

    if frappe.cache().get_value(event_id):
        return

    frappe.cache().set_value(event_id, True, expires_in_sec=60)

    # validate the webhook event
    event = frappe.form_dict.get("event")

    if not event or event not in SUPPORTED_EVENTS:
        log_integration_request(
            integration_request_service=f"RazorpayX Webhook Event - {event or 'Unknown'}",
            request_headers=str(frappe.request.headers),
            data=frappe.form_dict,
            error="The webhook event is not supported.",
            is_remote_request=True,
        )

        return

    # Process the webhook
    event_type = event.split(".")[0]

    if event_type == EVENTS_TYPE.PAYOUT.value:
        PayoutWebhook().process_webhook()
    elif event_type == EVENTS_TYPE.PAYOUT_LINK.value:
        PayoutLinkWebhook().process_webhook()
