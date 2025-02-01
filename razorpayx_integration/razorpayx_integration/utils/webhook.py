import json
from hmac import new as hmac

import frappe
from frappe import _
from frappe.utils import get_link_to_form, get_url_to_form
from frappe.utils.password import get_decrypted_password

from razorpayx_integration.constants import (
    RAZORPAYX_SETTING,
)
from razorpayx_integration.payment_utils.constants.enums import BaseEnum
from razorpayx_integration.payment_utils.utils import log_integration_request
from razorpayx_integration.razorpayx_integration.apis.payout import RazorpayXLinkPayout
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


###### WEBHOOK PROCESSORS ######
class RazorpayXWebhook:
    """
    Base class for RazorpayX Webhook Processor.
    """

    ### SETUP ###
    def __init__(
        self,
        payload: dict,
        integration_request: str,
        *args,
        **kwargs,
    ):
        """
        Initialize the attributes and setup the webhook payload.

        :param payload: Webhook payload data.
        :param integration_request: Integration Request name.
        """
        self.payload = payload
        self.integration_request = integration_request
        self.account_id = ""
        self.razorpayx_setting_name = ""

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

        self.set_razorpayx_setting_name()  # Mandatory
        self.set_common_payload_attributes()  # Mandatory
        self.setup_respective_webhook_payload()
        self.set_source_doctype_and_docname()

    def set_razorpayx_setting_name(self):
        """
        Set the RazorpayX Setting Name using the `account_id`.
        """
        if not self.account_id:
            self.account_id = self.payload.get("account_id")

        self.razorpayx_setting_name = get_razorpayx_setting(self.account_id)

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
            self.payload.get("payload", {}).get(self.event_type, {}).get("entity") or {}
        )

    def setup_respective_webhook_payload(self):
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

        self.notes = self.payload_entity.get("notes") or {}

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
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Webhook.

        It is entry point for the webhook processing.

        Note: 🟢 Override this method in the sub class for custom processing.
        """
        pass

    ### UTILITIES ###
    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Note: ⚠️ This method should be overridden in the sub class.
        """
        return True

    def get_ir_formlink(self, html: bool = False) -> str:
        """
        Get the Integration Request Form Link.

        :param html: bool - If True, return the anchor (<a>) tag.
        """
        if html:
            return get_link_to_form("Integration Request", self.integration_request)

        return get_url_to_form("Integration Request", self.integration_request)


class PayoutWebhook(RazorpayXWebhook):
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
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Payout Related Webhooks.
        """
        self.update_payment_entry()

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - Update the status of the Payment Entry.
        - Update the UTR Number.
        - If failed, cancel the Payment Entry and Payout Link.
        """
        if not self.should_update_payment_entry():
            return

        values = self.get_updated_reference()

        if self.id:
            values["razorpayx_payout_id"] = self.id

        self.source_doc.db_set(values, notify=True)
        self.update_payout_status(self.status)

        if self.should_cancel_payment_entry() and self.cancel_payout_link():
            self.cancel_payment_entry()

    ### UTILITIES ###
    def get_source_doc(self):
        """
        Get and Set the source doc.

        Fetch last created Payment Entry based on the id fields.

        - `Doctype` and `Docname` in the `notes` may be get cancelled and amended.
        """
        field_mapper = {
            EVENTS_TYPE.PAYOUT.value: "razorpayx_payout_id",
            EVENTS_TYPE.TRANSACTION.value: "razorpayx_payout_id",
            EVENTS_TYPE.PAYOUT_LINK.value: "razorpayx_payout_link_id",
        }

        if not self.id or not self.event_type:
            return

        id_field = field_mapper.get(self.event_type) or "razorpayx_payout_id"
        doctype = self.source_doctype or "Payment Entry"

        docname = frappe.db.get_value(
            doctype=doctype,
            filters={id_field: self.id},
            pluck="name",
            order_by="creation desc",
        )

        if not docname:
            return

        self.source_doc = frappe.get_doc(doctype, docname)

        return self.source_doc

    def should_update_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be updated or not.

        Note: Source doc (Payment Entry) is set here.
        """
        return bool(
            self.source_doctype == "Payment Entry"
            and self.get_source_doc()
            and self.is_order_maintained()
        )

    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Compare webhook status with the source docstatus and payout status.

        Note: 🟢 Override this method in the sub class for custom order maintenance.
        """
        pe_status = self.source_doc.razorpayx_payout_status.lower()

        return self.status and PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[pe_status]

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

    def update_payout_status(self, status: str | None = None):
        """
        Update RazorpayX Payout Status in Payment Entry.

        To trigger notification on change of status.

        :param status: Payout Webhook Status.
        """
        if not status:
            return

        self.source_doc.update({"razorpayx_payout_status": status.title()}).save()

    def cancel_payout_link(self) -> bool:
        """
        Cancel the Payout Link if the Payout is made from the Payout Link.

        :returns: bool - `True` if the Payout Link is cancelled successfully.
        """
        link_id = self.source_doc.razorpayx_payout_link_id

        if not link_id:
            return True

        try:
            payout_link = RazorpayXLinkPayout(self.razorpayx_setting_name)
            status = payout_link.get_by_id(link_id, "status")

            if self.is_payout_link_cancelled(status):
                return True

            if status == PAYOUT_LINK_STATUS.ISSUED.value:
                payout_link.cancel(
                    link_id,
                    source_doctype=self.source_doctype,
                    source_docname=self.source_docname,
                )

                return True

        except Exception:
            frappe.log_error(
                title="RazorpayX Payout Link Cancellation Failed",
                message=f"Source: {self.get_ir_formlink()}\n\n{frappe.get_traceback()}",
            )

    def cancel_payment_entry(self):
        """
        Cancel the Payment Entry.

        Set flags `__canceled_by_rpx` and cancel the Payment Entry.
        """
        self.source_doc.flags.__canceled_by_rpx = True
        self.source_doc.cancel()

    def should_cancel_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be cancelled or not.
        """
        if (
            self.status
            and self.source_doc.docstatus == 1
            and self.is_payout_cancelled(self.status)
        ):
            return True

    def is_payout_cancelled(self, status: str) -> bool:
        """
        Check if the Payout cancelled (cancelled, failed, rejected) or not.

        :param status: Payout Webhook Status.
        """
        return status in [
            PAYOUT_STATUS.CANCELLED.value,
            PAYOUT_STATUS.FAILED.value,
            PAYOUT_STATUS.REJECTED.value,
        ]

    def is_payout_link_cancelled(self, status: str) -> bool:
        """
        Check if the Payout Link cancelled (expired, rejected, cancelled) or not.

        :param status: Payout Link Webhook Status.
        """
        return status in [
            PAYOUT_LINK_STATUS.CANCELLED.value,
            PAYOUT_LINK_STATUS.EXPIRED.value,
            PAYOUT_LINK_STATUS.REJECTED.value,
        ]


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
        return bool(self.status)

    def update_payment_entry(self):
        """
        Update Payment Entry based on the webhook status.

        - If failed, cancel the Payment Entry.
            - Change Payment Status to `Cancelled`.
        """
        if not self.should_update_payment_entry():
            return

        values = self.get_updated_reference()

        if self.id:
            values["razorpayx_payout_link_id"] = self.id

        if values:
            self.source_doc.db_set(values, notify=True)

        if self.should_cancel_payment_entry():
            self.update_payout_status(PAYOUT_STATUS.CANCELLED.value)
            self.cancel_payment_entry()

    def should_cancel_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be cancelled or not.
        """
        if (
            self.status
            and self.source_doc.docstatus == 1
            and self.is_payout_link_cancelled()
        ):
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

    ### APIs ###
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Payout Related Webhooks.
        """
        self.update_payment_entry()
        self.update_bank_transaction()

    ### SETUP ###
    def setup_respective_webhook_payload(self):
        """
        Initialize the transaction webhook payload to be used in the webhook processing.

        ---
        Sample Payloads:
        - https://razorpay.com/docs/webhooks/payloads/x/transactions/#transaction-created
        """

        def get_payout_id() -> str:
            match self.transaction_type:
                case TRANSACTION_TYPE.PAYOUT.value:
                    return self.transaction_source.get("id")
                case TRANSACTION_TYPE.REVERSAL.value:
                    return self.transaction_source.get("payout_id")

        self.transaction_id = self.payload_entity.get("id")

        if self.payload_entity:
            self.transaction_source = self.payload_entity.get("source") or {}

        if self.transaction_source:
            self.transaction_type = self.transaction_source.get("entity")
            self.utr = self.transaction_source.get("utr")
            self.status = self.transaction_source.get("status")
            self.id = get_payout_id()
            self.notes = self.transaction_source.get("notes") or {}

    ### UTILITIES ###
    def is_order_maintained(self):
        """
        Check if the order is maintained or not.
        """
        valid_transaction = self.transaction_type in TRANSACTION_TYPE.values()

        if not self.status:
            return valid_transaction

        pe_status = self.source_doc.razorpayx_payout_status.lower()

        return (
            PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[pe_status] and valid_transaction
        )

    def update_payment_entry(self):
        if not self.should_update_payment_entry():
            return

        values = self.get_updated_reference()

        if self.id:
            values["razorpayx_payout_id"] = self.id

        self.source_doc.db_set(values)
        self.update_payout_status(self.status)

    def update_bank_transaction(self):
        """
        Update Bank Transaction based on the webhook entity.

        When Bank Transaction already created without `UTR` in `Processing` State.

        So, when `Processed` or `Reversed`, update the Bank Transaction with `UTR`.
        """
        if not self.utr or not self.transaction_id:
            return

        bank_transaction = frappe.db.exists(
            "Bank Transaction", {"transaction_id": self.transaction_id}
        )

        if not bank_transaction:
            return

        frappe.db.set_value(
            "Bank Transaction",
            bank_transaction,
            "reference_number",
            self.utr,
        )


class AccountWebhook(RazorpayXWebhook):
    """
    Processor for RazorpayX Account Webhook.

    Caution: ⚠️ Currently not supported.

    ---
    Reference: https://razorpay.com/docs/webhooks/payloads/x/account-validation/
    """

    pass


###### CONSTANTS ######
class TRANSACTION_TYPE(BaseEnum):
    """
    Available in transaction webhook Payload.

    - webhook data > payload > transaction > entity > source > entity
    """

    PAYOUT = "payout"  # when payout is created
    REVERSAL = "reversal"  # when payout is reversed


WEBHOOK_PROCESSORS_MAP = {
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

    It is the entry point for the RazorpayX Webhook.
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

    if not is_valid_webhook_signature(
        row_payload=row_payload,
        signature=signature,
        payload=payload,
        request_headers=request_headers,
    ):
        return

    ## Log the webhook request ##
    event = payload.get("event")
    ir_log = {
        "request_id": event_id,
        "status": "Completed",
        "integration_request_service": f"RazorpayX - {event or 'Unknown'}",
        "request_headers": request_headers,
        "data": payload,
        "is_remote_request": True,
    }

    if unsupported_event := is_unsupported_event(event):
        ir_log["error"] = "Unsupported Webhook Event"
        ir_log["status"] = "Cancelled"

    ir = log_integration_request(**ir_log)

    ## Return if the event is unsupported ##
    if unsupported_event:
        return

    ## Process the webhook ##
    frappe.enqueue(
        process_razorpayx_webhook,
        payload=payload,
        integration_request=ir.name,
        now=frappe.conf.developer_mode,
    )


def process_razorpayx_webhook(payload: dict, integration_request: str):
    """
    Process the RazorpayX Webhook.

    :param payload: Webhook payload data.
    :param integration_request: Integration Request docname.
    """

    event_type = payload["event"].split(".")[0]  # `event` must be exist

    # Getting the webhook processor based on the event type.
    processor = WEBHOOK_PROCESSORS_MAP[event_type](payload, integration_request)
    processor.process_webhook()


###### UTILITIES ######
def is_valid_webhook_signature(
    row_payload: bytes,
    signature: str,
    *,
    payload: dict | None = None,
    request_headers: str | None = None,
) -> bool:
    """
    Check if the RazorpayX Webhook Signature is valid or not.

    :param row_payload: Raw payload data (Do not parse the data).
    :param request_headers: Request headers.
    :param payload: Parsed payload data.
    :param signature: Webhook Signature
    """

    def get_expected_signature(secret: str) -> str:
        return hmac(secret.encode(), row_payload, "sha256").hexdigest()

    if not payload:
        payload = json.loads(row_payload)

    if not request_headers:
        request_headers = str(frappe.request.headers)

    webhook_secret = get_webhook_secret(payload.get("account_id"))

    try:
        if not webhook_secret:
            raise Exception("RazorpayX Webhook Secret Not Found")

        if signature != get_expected_signature(webhook_secret):
            raise Exception("RazorpayX Webhook Signature Mismatch")

        return True

    except Exception:
        divider = f"\n\n{'-' * 25}\n\n"
        message = f"Request Headers:\n{request_headers.strip()}"
        message += divider
        message += f"Webhook Payload:\n{frappe.as_json(payload, indent=2)}"
        message += divider
        message += f"{frappe.get_traceback()}"

        frappe.log_error(
            title="Invalid RazorpayX Webhook Signature",
            message=message,
        )

        return False


@frappe.request_cache
def get_razorpayx_setting(account_id: str) -> str | None:
    """
    Fetch the RazorpayX Integration Setting name based on the identifier.

    :param account_id: RazorpayX Account ID (Business ID).
    """
    if account_id.startswith("acc_"):
        account_id = account_id.removeprefix("acc_")

    return frappe.db.get_value(
        doctype=RAZORPAYX_SETTING,
        filters={
            "account_id": account_id,
        },
    )


def get_webhook_secret(account_id: str | None = None) -> str | None:
    """
    Get the webhook secret from the account id.

    :param account_id: RazorpayX Account ID (Business ID).

    ---
    Note: `account_id` should be in the format `acc_XXXXXX`.
    """
    if not account_id:
        return

    setting = get_razorpayx_setting(account_id)

    if not setting:
        return

    return get_decrypted_password(RAZORPAYX_SETTING, setting, "webhook_secret")
