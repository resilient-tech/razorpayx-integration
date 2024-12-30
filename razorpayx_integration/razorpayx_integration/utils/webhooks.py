import json
from hmac import new as hmac

import frappe
from frappe import _
from frappe.utils import get_link_to_form, get_url_to_form
from frappe.utils.password import get_decrypted_password

from razorpayx_integration.constants import (
    RAZORPAYX_INTEGRATION_DOCTYPE,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
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
    """

    ### SETUP ###
    def __init__(self):
        """
        Initialize the attributes.
        """
        self.payload = {}
        self.integration_request = ""
        self.account_id = ""
        self.razorpayx_account = ""

        self.event = ""
        self.event_type = ""

        self.payload_entity = {}
        self.status = ""
        self.utr = ""
        self.id = ""

        self.source_docname = ""
        self.source_doctype = ""
        self.source_doc = None  # Set manually in the sub class if needed.
        self.notes = {}

    def setup_webhook_payload(self):
        """
        Setup the webhook payload data to be used in the webhook processing.

        Note: 🟢 Override this method in the sub class for custom payload setup.
        ---
        Sample Payloads:

        - Payout: https://razorpay.com/docs/webhooks/payloads/x/payouts/#payout-pending
        - Payout Link: https://razorpay.com/docs/webhooks/payloads/x/payout-links/#payout-linkrejected
        - Transaction: https://razorpay.com/docs/webhooks/payloads/x/transactions/#transaction-created
        - Account Validation: https://razorpay.com/docs/webhooks/payloads/x/account-validation/#fund-accountvalidationcompleted
        """
        if self.payload_entity:
            self.status = self.payload_entity.get("status")
            self.utr = self.payload_entity.get("utr")
            self.id = self.payload_entity.get("id")

        self.notes = self.payload_entity.get("notes", {})
        self.set_source_doctype_and_docname()

    def set_common_payload_attributes(self):
        """
        Set the common payload attributes.

        Attributes which are common in all webhook payloads.

        ---
        Common Attributes:
        - `event`
        - `event_type`
        - `payload_entity`
        """
        self.event = self.payload["event"]
        self.event_type = self.event.split(".")[0]

        self.payload_entity = (
            self.payload.get("payload", {}).get(self.event_type, {}).get("entity", {})
        )

    def set_razorpayx_account(self):
        """
        Set the RazorpayX Account Docname using the `account_id`.
        """
        if not self.account_id:
            self.account_id = self.payload.get("account_id")

        self.razorpayx_account = get_account_integration_name(self.account_id)

    def set_source_doctype_and_docname(self):
        """
        Set the source doctype and docname.

        Fetching from `notes`.
        """
        if self.notes and isinstance(self.notes, dict):
            self.source_doctype = self.notes.get("source_doctype", "")
            self.source_docname = self.notes.get("source_docname", "")

    def get_source_doc(self):
        """
        Get the source doc.

        Also set the source doc if not set.

        Note: Call this manually in the sub class if needed, because the source doc
        is not set in the `setup_webhook_payload` method.
        """
        if not self.source_doctype or not self.source_docname:
            return

        self.source_doc = frappe.get_doc(self.source_doctype, self.source_docname)

        return self.source_doc

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
        - Don't forget to call `super().process_webhook()` in the sub class.
        """
        self.payload = payload
        self.integration_request = integration_request
        self.account_id = account_id

        self.set_razorpayx_account()  # Mandatory
        self.set_common_payload_attributes()  # Mandatory
        self.setup_webhook_payload()

    ### UTILITIES ###

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Note: This method should be overridden in the sub class.
        """
        pass

    def get_ir_formlink(self, html: bool = False) -> str:
        """
        Get the Integration Request Form Link.

        :param html: bool - If True, return the HTML link.
        """
        if html:
            return get_link_to_form("Integration Request", self.integration_request)

        return get_url_to_form("Integration Request", self.integration_request)


class PayoutWebhook(RazorPayXWebhook):
    """
    Processor for RazorpayX Payout Webhook.

    - Update the Payment Entry based on the webhook status.

    ---
    Supported webhook events(8):

    - payout.pending
    - payout.processing
    - payout.queued
    - payout.initiated
    - payout.processed
    - payout.reversed
    - payout.failed
    - payout.updated

    ---
    Reference: https://razorpay.com/docs/webhooks/payloads/x/payouts/
    """

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

        self.update_payment_entry()

    ### UTILITIES ###
    def should_update_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be updated or not.

        Note: Source doc (Payment Entry) is set here.
        """
        return (
            self.source_doctype == "Payment Entry"
            and self.source_docname
            and self.get_source_doc()
            and self.is_order_maintained()
        )

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Compare webhook status with the source docstatus and payout status.

        Note: 🟢 Override this method in the sub class for custom order maintenance.
        """
        pe_status = self.source_doc.razorpayx_payout_link_status.lower()

        return (
            self.status
            and self.source_doc.docstatus == 1
            and PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[pe_status]
        )

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - Update the status of the Payment Entry.
        - Update the UTR Number.
        - If failed, cancel the Payment Entry and Payout Link.
        """
        if not self.should_update_payment_entry():
            return

        values = {
            "razorpayx_payout_status": self.status.title(),
            **self.get_updated_reference(),
        }

        if self.id:
            values["razorpayx_payout_id"] = self.id

        self.source_doc.db_set(values, notify=True)

        if self.should_cancel_payment_entry() and self.payout_link_cancelled():
            self.cancel_payment_entry()

    def get_updated_reference(self) -> dict:
        """
        Get PE's `reference_no` and `remarks` based on the UTR.
        """

        def get_new_remarks() -> str:
            return self.source_doc.remarks.replace(
                self.source_doc.reference_no, self.utr
            )

        if not self.utr:
            return {}

        return {
            "reference_no": self.utr,
            "remarks": get_new_remarks(),
        }

    def payout_link_cancelled(self) -> bool:
        """
        Cancel the Payout Link.

        :returns: bool - `True` if the Payout Link is cancelled successfully.
        """
        if not self.source_doc.razorpayx_payout_link_id:
            return True

        try:
            payout_link = RazorPayXLinkPayout(self.razorpayx_account)
            link_id = self.source_doc.razorpayx_payout_link_id

            status = payout_link.get_by_id(link_id, "status")

            if status in [
                PAYOUT_LINK_STATUS.CANCELLED.value,
                PAYOUT_LINK_STATUS.EXPIRED.value,
                PAYOUT_LINK_STATUS.REJECTED.value,
            ]:
                return True

            if status == PAYOUT_LINK_STATUS.ISSUED.value:
                payout_link.cancel(link_id)
                return True

        except Exception:
            frappe.log_error(
                title="RazorpayX Payout Link Cancellation Failed",
                message=f"Source: {self.get_ir_formlink()}\n\n{frappe.get_traceback()}",
            )

    def cancel_payment_entry(self):
        """
        Cancel the Payment Entry.
        """
        self.source_doc.flags.__canceled_by_rpx = True
        self.source_doc.cancel()

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


class PayoutLinkWebhook(PayoutWebhook):
    """
    Processor for RazorpayX Payout Link Webhook.

    - Update the Payment Entry based on the webhook status.

    ---
    Supported webhook events(3):

    - payout_link.cancelled
    - payout_link.expired
    - payout_link.rejected

    ---
    Reference: https://razorpay.com/docs/webhooks/payloads/x/payout-links/
    """

    ### UTILITIES ###
    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Caution: ⚠️ Payout link status is not maintained in the Payment Entry.
        """
        return self.status and self.source_doc.docstatus == 1

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - Update the UTR Number.
        - If failed, cancel the Payment Entry.
            - Change Payment Status to `Cancelled`.
        """
        if not self.should_update_payment_entry():
            return

        values = self.get_updated_reference()

        cancel_pe = self.should_cancel_payment_entry()

        if cancel_pe:
            values["razorpayx_payout_status"] = PAYOUT_STATUS.CANCELLED.value

        if self.id:
            values["razorpayx_payout_link_id"] = self.id

        self.source_doc.db_set(values, notify=True)

        if cancel_pe:
            self.cancel_payment_entry()

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


class TransactionWebhook(PayoutWebhook):
    """
    Processor for RazorpayX Transaction Webhook.

    - Update the Payment Entry based on the webhook entity.
        - Update PE status
        - Update UTR Number
        - Cancel the PE if failed.

    ---
    - Supported webhook events(1):
        - transaction.created
            - payout created
            - payout reversed

    ---
    Reference: https://razorpay.com/docs/webhooks/payloads/x/transactions/
    """

    ### SETUP ###
    def setup_webhook_payload(self):
        """
        Initialize the transaction webhook payload to be used in the webhook processing.

        ---
        Sample Payloads:
        - https://razorpay.com/docs/webhooks/payloads/x/transactions/#transaction-created
        """

        def get_status() -> str:
            if status := self.transaction_source.get("status"):
                return status

            match self.transaction_type:
                case TRANSACTION_TYPES.PAYOUT.value:
                    return PAYOUT_STATUS.PROCESSING.value
                case TRANSACTION_TYPES.REVERSAL.value:
                    return PAYOUT_STATUS.REVERSED.value

        def get_payout_id() -> str:
            match self.transaction_type:
                case TRANSACTION_TYPES.PAYOUT.value:
                    return self.transaction_source.get("id")
                case TRANSACTION_TYPES.REVERSAL.value:
                    return self.transaction_source.get("payout_id")

        if self.payload_entity:
            self.transaction_source = self.payload_entity.get("source", {})

        if self.transaction_source:
            self.transaction_type = self.transaction_source.get("entity")
            self.utr = self.transaction_source.get("utr")
            self.status = get_status()
            self.id = get_payout_id()

    ### UTILITIES ###
    def is_order_maintained(self):
        """
        Check if the order maintained or not.
        """
        return bool(
            self.status
            and self.source_doc.docstatus == 1
            and self.transaction_type in TRANSACTION_TYPES.values()
        )

    def update_payment_entry(self):
        if not self.should_update_payment_entry():
            return

        values = self.get_updated_reference()

        if self.status:
            values["razorpayx_payout_status"] = self.status.title()

        if self.id:
            values["razorpayx_payout_id"] = self.id

        self.source_doc.db_set(values, notify=True)

        if self.should_cancel_payment_entry() and self.payout_link_cancelled():
            self.cancel_payment_entry()

    def should_cancel_payment_entry(self):
        return (
            self.source_doc.docstatus == 1
            and self.status
            and self.status == PAYOUT_STATUS.REVERSED.value
        )


class AccountWebhook(RazorPayXWebhook):
    """
    Processor for RazorpayX Account Webhook.

    Caution: ⚠️ Currently not supported.
    """

    pass


###### CONSTANTS ######
WEBHOOK_EVENT_TYPES_MAPPER = {
    EVENTS_TYPE.PAYOUT.value: PayoutWebhook,
    EVENTS_TYPE.PAYOUT_LINK.value: PayoutLinkWebhook,
    EVENTS_TYPE.TRANSACTION.value: TransactionWebhook,
    EVENTS_TYPE.ACCOUNT.value: AccountWebhook,
}


class TRANSACTION_TYPES(BaseEnum):
    """
    Available in transaction webhook Payload.

    - request data > payload > transaction > entity > source > entity
    """

    PAYOUT = "payout"  # when payout is created
    REVERSAL = "reversal"  # when payout is reversed


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

    account_id = validate_webhook_signature(
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
    #     account_id=account_id,
    # )

    # TODO: remove this line after testing
    process_razorpayx_webhook(event, payload, ir.name, account_id)


def process_razorpayx_webhook(
    event: str, payload: dict, integration_request: str, account_id: str | None = None
):
    """
    Process the RazorpayX Webhook.

    :param event: Webhook event.
    :param payload: Webhook payload data.
    :param integration_request: Integration Request docname.
    :param account_id: RazorpayX Account ID (Business ID).
        - Must be start with `acc_`.
    """

    event_type = event.split(".")[0]

    # To make it readable
    if event_type == EVENTS_TYPE.PAYOUT.value:
        processor = PayoutWebhook()
    elif event_type == EVENTS_TYPE.PAYOUT_LINK.value:
        processor = PayoutLinkWebhook()
    elif event_type == EVENTS_TYPE.TRANSACTION.value:
        processor = TransactionWebhook()
    else:
        processor = AccountWebhook()

    processor.process_webhook(payload, integration_request, account_id)


###### UTILITIES ######
def validate_webhook_signature(
    row_payload: bytes,
    signature: str,
    *,
    payload: dict | None = None,
    request_headers: str | None = None,
) -> str | None:
    """
    Validate the RazorpayX Webhook Signature.

    :param row_payload: Raw payload data (Do not parse the data).
    :param request_headers: Request headers.
    :param payload: Parsed payload data.
    :param signature: Header signature.

    :returns: RazorpayX Account ID.
    """
    if not payload:
        payload = json.loads(row_payload)

    if not request_headers:
        request_headers = str(frappe.request.headers)

    account_id = payload.get("account_id")
    webhook_secret = get_webhook_secret(account_id)

    try:
        expected_signature = hmac(
            webhook_secret.encode(), row_payload, "sha256"
        ).hexdigest()

        if signature != expected_signature:
            raise Exception

        return account_id
    except Exception:
        frappe.log_error(
            title="Invalid RazorPayX Webhook Signature",
            message=f"Webhook Payload:\n{frappe.as_json(payload,indent=2)}\n\n---\n\nRequest Headers:\n{request_headers}",
        )

        frappe.throw(msg=_("Invalid RazorPayX Webhook Signature"))


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
