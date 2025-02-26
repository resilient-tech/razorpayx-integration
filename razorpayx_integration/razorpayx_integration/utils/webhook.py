import json
from hmac import new as hmac

import frappe
import frappe.utils
from frappe import _
from frappe.utils import fmt_money, get_link_to_form, get_url_to_form, today
from frappe.utils.password import get_decrypted_password
from payment_integration_utils.payment_integration_utils.constants.enums import BaseEnum
from payment_integration_utils.payment_integration_utils.utils import (
    log_integration_request,
    paisa_to_rupees,
)

from razorpayx_integration.constants import RAZORPAYX_SETTING
from razorpayx_integration.razorpayx_integration.apis.payout import RazorpayXLinkPayout
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_CURRENCY,
    PAYOUT_LINK_STATUS,
    PAYOUT_ORDERS,
    PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    EVENTS_TYPE,
    SUPPORTED_EVENTS,
)


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
        self.id_field = ""

        self.payload_entity = {}
        self.status = ""
        self.utr = ""
        self.id = ""

        self.source_docname = ""
        self.source_doctype = ""
        self.source_doc = frappe._dict()  # Set manually in the sub class if needed.
        self.referenced_docnames = []
        self.notes = {}

        self.set_razorpayx_setting_name()  # Mandatory
        self.set_common_payload_attributes()  # Mandatory
        self.setup_respective_webhook_payload()
        self.set_source_doctype_and_docname()
        self.set_id_field()

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
        is not set in the `setup_respective_webhook_payload` method.
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

    def set_id_field(self):
        """
        set the integration payout related ID field.

        Helpful for fetching reference docs and updating the data.
        """
        pass

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
        self.create_journal_entry()

    def update_payment_entry(self, update_status: bool = True):
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
            values[self.id_field] = self.id

        if values:
            self.source_doc.db_set(values, notify=True)
            self.update_referenced_pes(values, self.status)

        if update_status:
            self.update_payout_status(self.status)

        self.handle_pe_cancellation()

    def update_payout_status(self, status: str | None = None):
        """
        Update RazorpayX Payout Status in Payment Entry.

        To trigger notification on change of status.

        :param status: Payout Webhook Status.
        """

        if not status or status not in PAYOUT_STATUS.values():
            return

        value = {"razorpayx_payout_status": status.title()}

        if self.source_doc.docstatus == 2:
            self.source_doc.db_set(value, notify=True)
        else:
            self.source_doc.update(value).save()

    def update_referenced_pes(self, values: dict, status: str | None = None):
        """
        Update the referenced payment entries.

        :param values: dict - Values to be updated.
        :param status: str - Webhook Payout Status.
        """
        if not self.referenced_docnames:
            return

        if status:
            values["razorpayx_payout_status"] = status.title()

        frappe.db.set_value(
            "Payment Entry", {"name": ["in", set(self.referenced_docnames)]}, values
        )

    def handle_pe_cancellation(self):
        """
        Handle the payment entry cancellation.

        - Cancel the Payment Entry if the payout is failed.
        - Cancel the Payout Link if the payout is made from the Payout Link.
        """
        if self.should_cancel_payment_entry() and self.cancel_payout_link():
            self.cancel_payment_entry()

    def create_journal_entry(self):
        """
        Create a Journal Entry for the Payout Charges (fees + tax).

        Reference: https://razorpay.com/docs/x/manage-teams/billing/
        """

        def fmt_inr(amount: int) -> str:
            return fmt_money(amount, currency=PAYOUT_CURRENCY.INR.value)

        if self.status != PAYOUT_STATUS.PROCESSED.value:
            return

        fees = self.payload_entity.get("fees") or 0
        tax = self.payload_entity.get("tax") or 0
        charges = fees + tax

        if charges == 0:
            return

        fee_type = self.payload_entity.get("fee_type")
        charges = paisa_to_rupees(charges)

        expense_account, payable_account = frappe.db.get_value(
            RAZORPAYX_SETTING,
            self.razorpayx_setting_name,
            ["expense_account", "payable_account"],
        )

        user_remark = (
            f"{self.source_doc.doctype}: {self.source_doc.name}\n"
            if self.source_doc
            else ""
        )
        user_remark = f"Payout ID: {self.id}"
        user_remark += f"\nFee Type: {fee_type}" if fee_type else ""
        user_remark += f"\nFees: {fmt_inr(fees)} | Tax: {fmt_inr(tax)}"
        user_remark += f"\nIntegration Request: {self.get_ir_formlink(html=True)}"

        je = frappe.new_doc("Journal Entry")
        je.update(
            {
                "voucher_type": "Journal Entry",
                "posting_date": self.payload.get("created_at") or today(),
                "accounts": [
                    {
                        "account": expense_account,
                        "debit_in_account_currency": charges,
                        "credit_in_account_currency": 0,
                    },
                    {
                        "account": payable_account,
                        "debit_in_account_currency": 0,
                        "credit_in_account_currency": charges,
                    },
                ],
                "cheque_no": self.utr,
                "user_remark": user_remark,
            }
        )

        je.submit()

    ### UTILITIES ###
    def set_id_field(self) -> str:
        field_mapper = {
            EVENTS_TYPE.PAYOUT.value: "razorpayx_payout_id",
            EVENTS_TYPE.TRANSACTION.value: "razorpayx_payout_id",
            EVENTS_TYPE.PAYOUT_LINK.value: "razorpayx_payout_link_id",
        }

        self.id_field = field_mapper.get(self.event_type) or "razorpayx_payout_id"

    def get_source_doc(self):
        """
        Get and Set the source doc.

        - Fetch last created Doc based on the id fields.
        - If not fetched by ID, find by source doctype and docname.
        - Set Other referenced docnames.
        """
        if not self.id or not self.event_type:
            return

        doctype = self.source_doctype or "Payment Entry"
        docnames = []

        if self.id_field:
            docnames = frappe.db.get_all(
                doctype=doctype,
                filters={self.id_field: self.id},
                pluck="name",
                order_by="creation desc",
            )

        if not docnames:
            # payout maybe made from the Payout Link so find the doc by source docname and doctype
            if not self.source_doctype or not self.source_docname:
                return

            docnames = get_referenced_docnames(self.source_doctype, self.source_docname)

        # references are not available
        if not docnames:
            return

        self.source_doc = frappe.get_doc(doctype, docnames[0], for_update=True)
        self.referenced_docnames = docnames[1:]  # to avoid updating the same doc

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

        if not self.utr:
            return {}

        return {
            "reference_no": self.utr,
            "remarks": self.source_doc.remarks.replace(
                self.source_doc.reference_no, self.utr
            ),
        }

    ### CANCELLATION ###
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
        return (
            self.status
            and self.source_doc.docstatus == 1
            and self.is_payout_cancelled(self.status)
        )

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

    ### APIs ###
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Payout Link Related Webhooks.
        """
        self.update_payment_entry(update_status=False)

    def handle_pe_cancellation(self):
        if self.should_cancel_payment_entry():
            self.update_payout_status(PAYOUT_STATUS.CANCELLED.value)
            self.cancel_payment_entry()

    ### UTILITIES ###
    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Caution: ⚠️ Payout link status is not maintained in the Payment Entry.
        """
        return bool(self.status)

    def should_cancel_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be cancelled or not.
        """
        return (
            self.status
            and self.source_doc.docstatus == 1
            and self.is_payout_link_cancelled()
        )


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

    ### APIs ###
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Payout Related Webhooks.
        """
        self.update_payment_entry()
        self.update_bank_transaction()

    def handle_pe_cancellation(self):
        pass

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

    ### UTILITIES ###
    def is_order_maintained(self):
        """
        Check if the order is maintained or not.
        """
        is_valid_transaction = self.transaction_type in TRANSACTION_TYPE.values()

        # if status not available, depend on the type
        if not self.status or not is_valid_transaction:
            return is_valid_transaction

        # if status available, compare with the source doc payout status
        pe_status = self.source_doc.razorpayx_payout_status.lower()
        return PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[pe_status]


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

    # Process the webhook ##
    frappe.enqueue(
        process_razorpayx_webhook,
        payload=payload,
        integration_request=ir.name,
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


def get_referenced_docnames(doctype: str, docname: str) -> list[str] | None:
    """
    Get the referenced docnames based.

    - Order by creation date.

    :param doctype: Source Doctype.
    :param docname: Source Docname.
    """
    docstatus = frappe.db.get_value(
        doctype,
        docname,
        "docstatus",
    )

    # document does not exist
    if docstatus is None:
        return

    if docstatus != 2 or not frappe.db.exists(doctype, {"amended_from": docname}):
        return [docname]

    docnames = [docname]

    # document is cancelled and amended
    while True:
        amended = frappe.db.get_value(
            doctype,
            {"amended_from": docname},
            ["name", "docstatus"],
            as_dict=True,
        )

        if not amended:
            break

        if amended.docstatus != 2:
            docnames.insert(0, amended.name)
            break

        docname = amended.name
        docnames.insert(0, docname)

    return docnames
