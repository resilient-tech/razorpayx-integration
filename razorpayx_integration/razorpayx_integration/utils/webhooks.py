import json
from hmac import new as hmac

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe import _
from frappe.utils import get_link_to_form, get_url_to_form
from frappe.utils.password import get_decrypted_password

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
    """
    Base class for RazorpayX Webhook Processor.

    Note: This class should be inherited by the webhook processor classes.
    """

    ### SETUP ###
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

    ### APIs ###
    def process_webhook(
        self, payload: dict, integration_request: str, account_id: str | None = None
    ):
        """
        Process RazorpayX Webhook.

        :param payload: Webhook payload data.
        :param integration_request: Integration Request name.
        :param account_id: RazorpayX Account ID (Business ID).

        ---
        Note:
        - This method should be overridden in the sub class.
        - Don't forget to call `super().process_webhook()` in the sub class.
        """
        self.payload = payload
        self.integration_request = integration_request
        self.account_id = account_id

        if not self.account_id:
            self.account_id = self.payload.get("account_id")

        self.razorpayx_account = get_account_integration_name(self.account_id)

        self.initialize_payload_data()

    ### UTILITIES ###
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
    def process_webhook(
        self, payload: dict, integration_request: str, account_id: str | None = None
    ):
        """
        Process RazorpayX Payout Webhook.

        :param payload: Webhook payload data.
        :param integration_request: Integration Request name.
        :param account_id: RazorpayX Account ID (Business ID).
        """
        super().process_webhook(
            payload=payload,
            integration_request=integration_request,
            account_id=account_id,
        )

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

        def get_new_remarks() -> str:
            return self.source_doc.remarks.replace(
                self.source_doc.reference_no, self.utr
            )

        values = {
            "razorpayx_payment_status": self.status.title(),
        }

        if self.utr:
            values["reference_no"] = self.utr

            if self.source_doc.remarks:
                values["remarks"] = get_new_remarks()

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
            payout_link = RazorPayXLinkPayout(self.razorpayx_account)
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
                message=f"Source: {self.get_ir_formlink()}\n\n{frappe.get_traceback()}",
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
    def process_webhook(
        self, payload: dict, integration_request: str, account_id: str | None = None
    ):
        """
        Process RazorpayX Payout Link Webhook.

        :param payload: Webhook payload data.
        :param integration_request: Integration Request name.
        """
        super().process_webhook(
            payload=payload,
            integration_request=integration_request,
            account_id=account_id,
        )

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

        def get_new_remarks() -> str:
            return self.source_doc.remarks.replace(
                self.source_doc.reference_no, self.utr
            )

        values = {}

        cancel_pe = self.should_cancel_payment_entry()

        if cancel_pe:
            values["razorpayx_payment_status"] = PAYOUT_STATUS.CANCELLED.value

        if self.utr:
            values["reference_no"] = self.utr

            if self.source_doc.remarks:
                values["remarks"] = get_new_remarks()

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


# TODO: Transaction Webhook
# Handle only 2: `reversal` and `payout_failed`
# Ref1: http://razorpayx.localhost:8001/app/integration-request/5lgv3tbdn6 (reversal)
# ref2: http://razorpayx.localhost:8001/app/integration-request/u7k9okob4m (created)
class TransactionWebhook(RazorPayXWebhook):
    pass


class AccountWebhook(RazorPayXWebhook):
    pass


###### CONSTANTS ######
WEBHOOK_EVENT_TYPES_MAPPER = {
    EVENTS_TYPE.PAYOUT.value: PayoutWebhook,
    EVENTS_TYPE.PAYOUT_LINK.value: PayoutLinkWebhook,
    EVENTS_TYPE.TRANSACTION.value: TransactionWebhook,
    EVENTS_TYPE.ACCOUNT.value: AccountWebhook,
}


###### APIs ######
@frappe.whitelist(allow_guest=True)
def razorpayx_webhook_listener():
    """
    RazorpayX Webhook Listener.
    """

    def is_unsupported_event(event: str | None) -> bool:
        return bool(not event or event not in SUPPORTED_EVENTS)

    ## Check if the event is already processed ##
    event_id = frappe.get_request_header("X-Razorpay-Event-Id")
    signature = frappe.get_request_header("X-Razorpay-Signature")

    if not (event_id and signature):
        return

    if frappe.cache().get_value(event_id):
        return

    frappe.cache().set_value(event_id, True, expires_in_sec=60)

    ## Validate the webhook signature ##
    frappe.set_user("Administrator")
    row_payload = frappe.request.data
    payload = json.loads(row_payload)
    request_headers = str(frappe.request.headers)

    validate_webhook_signature(
        row_payload, signature, payload=payload, request_headers=request_headers
    )

    ## Log the webhook request ##
    event = payload.get("event")
    ir_log = {
        "request_id": event_id,
        "status": "Completed",
        "integration_request_service": f"RazorpayX Webhook Event - {event or 'Unknown'}",
        "request_headers": request_headers,
        "data": payload,
        "is_remote_request": True,
    }

    if unsupported_event := is_unsupported_event(event):
        ir_log["error"] = "Unsupported Webhook Event"
        ir_log["status"] = "Cancelled"

    ir = log_integration_request(**ir_log)

    ## Process the webhook ##
    if unsupported_event:
        return

    # TODO: enqueue the webhook processing
    # frappe.enqueue(
    #     process_razorpayx_webhook,
    #     event=event,
    #     payload=payload,
    #     integration_request=ir.name,
    # )

    # TODO: remove this line after testing
    process_razorpayx_webhook(event=event, payload=payload, integration_request=ir.name)


def process_razorpayx_webhook(event: str, payload: dict, integration_request: str):
    """
    Process the RazorpayX Webhook.

    :param event: Webhook event.
    :param payload: Webhook payload data.
    :param integration_request: Integration Request docname.
    """

    def get_webhook_processor() -> (
        PayoutWebhook | PayoutLinkWebhook | TransactionWebhook | AccountWebhook
    ):
        """
        Get the webhook processor based on the event type.
        """
        event_type = event.split(".")[0]
        return WEBHOOK_EVENT_TYPES_MAPPER.get(event_type)()

    get_webhook_processor().process_webhook(
        payload=payload,
        integration_request=integration_request,
        account_id=payload.get("account_id"),
    )


###### UTILITIES ######
def validate_webhook_signature(
    row_payload: bytes,
    signature: str,
    *,
    payload: dict | None = None,
    request_headers: str | None = None,
):
    """
    Validate the RazorpayX Webhook Signature.

    :param row_payload: Raw payload data (Do not parse the data).
    :param request_headers: Request headers.
    :param payload: Parsed payload data.
    :param signature: Header signature.

    """
    if not payload:
        payload = json.loads(row_payload)

    if not request_headers:
        request_headers = str(frappe.request.headers)

    webhook_secret = get_webhook_secret(payload.get("account_id"))

    try:
        expected_signature = hmac(
            webhook_secret.encode(), row_payload, "sha256"
        ).hexdigest()

        if signature != expected_signature:
            raise Exception

    except Exception:
        frappe.log_error(
            title="Invalid RazorPayX Webhook Signature",
            message=f"Webhook Payload:\n{frappe.as_json(payload,indent=2)}\n\n---\n\nRequest Headers:\n{request_headers}",
        )

        frappe.throw(_("Invalid RazorPayX Webhook Signature"))


def get_webhook_secret(account_id: str) -> str | None:
    """
    Get the webhook secret from the account id.

    :param account_id: RazorpayX Account ID (Business ID).

    ---
    Note: `account_id` should be in the format `acc_XXXXXX`.
    """
    name = get_account_integration_name(account_id)

    return get_decrypted_password(RAZORPAYX_INTEGRATION_DOCTYPE, name, "webhook_secret")


@frappe.request_cache
def get_account_integration_name(account_id: str) -> str | None:
    """
    Get the account integration name from the account id.

    :param account_id: RazorpayX Account ID (Business ID).

    ---
    Note: `account_id` should be in the format `acc_XXXXXX`.
    """
    account_id = account_id.removeprefix("acc_")

    return frappe.get_value(
        RAZORPAYX_INTEGRATION_DOCTYPE,
        {"account_id": account_id},
        "name",
    )
