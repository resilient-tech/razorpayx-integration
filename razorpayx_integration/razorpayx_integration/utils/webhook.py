import json
from hmac import new as hmac
from typing import Literal

import frappe
import frappe.utils
from erpnext.accounts.doctype.journal_entry.journal_entry import (
    make_reverse_journal_entry,
)
from erpnext.accounts.doctype.unreconcile_payment.unreconcile_payment import (
    create_unreconcile_doc_for_selection,
)
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import fmt_money, get_link_to_form, get_url_to_form, today
from frappe.utils.password import get_decrypted_password
from payment_integration_utils.payment_integration_utils.constants.enums import BaseEnum
from payment_integration_utils.payment_integration_utils.utils import (
    get_str_datetime_from_epoch as get_epoch_date,
)
from payment_integration_utils.payment_integration_utils.utils import (
    log_integration_request,
    paisa_to_rupees,
)

from razorpayx_integration.constants import RAZORPAYX_CONFIG
from razorpayx_integration.razorpayx_integration.apis.payout import RazorpayXLinkPayout
from razorpayx_integration.razorpayx_integration.constants.payouts import (
    PAYOUT_CURRENCY,
    PAYOUT_FROM,
    PAYOUT_LINK_STATUS,
    PAYOUT_ORDERS,
    PAYOUT_STATUS,
)
from razorpayx_integration.razorpayx_integration.constants.webhooks import (
    EVENTS_TYPE,
    SUPPORTED_EVENTS,
)
from razorpayx_integration.razorpayx_integration.utils import (
    get_fees_accounting_config,
    is_create_je_on_reversal_enabled,
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
        self.config_name = ""

        self.event = ""
        self.event_type = ""
        self.id_field = ""

        self.payload_entity = {}
        self.status = ""  # Payout Status
        self.utr = ""
        self.id = ""  # Payout ID
        self.reversal_id = ""

        self.source_docname = ""
        self.source_doctype = ""
        self.source_doc = frappe._dict()  # Set manually in the sub class if needed.
        self.referenced_docnames = []
        self.notes = {}

        self.order_maintained = False

        self.set_config_name()  # Mandatory
        self.set_common_payload_attributes()  # Mandatory
        self.setup_respective_webhook_payload()
        self.set_source_doctype_and_docname()
        self.set_id_field()

    def set_config_name(self):
        """
        Set the RazorpayX Configuration Name using the `account_id`.
        """
        if not self.account_id:
            self.account_id = self.payload.get("account_id")

        self.config_name = get_razorpayx_config(self.account_id)

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
        if not self.payload_entity or not isinstance(self.payload_entity, dict):
            return

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

    def get_formlink(self, doctype: str, docname: str, html: bool = False) -> str:
        return (
            get_link_to_form(doctype, docname)
            if html
            else get_url_to_form(doctype, docname)
        )

    def get_ir_formlink(self, html: bool = False) -> str:
        """
        Get the Integration Request Form Link.

        :param html: bool - If True, return the anchor (<a>) tag.
        """
        return self.get_formlink("Integration Request", self.integration_request, html)

    def get_source_formlink(self, html: bool = False) -> str | None:
        """
        Get the Source Doc Form Link.

        :param html: bool - If True, return the anchor (<a>) tag.
        """
        if not self.source_doc:
            return

        return self.get_formlink(self.source_doc.doctype, self.source_doc.name, html)


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

        if not self.source_doc or not self.order_maintained:
            return

        self.create_journal_entry_for_fees()

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

        self.handle_failure()

    def update_payout_status(self, status: str | None = None):
        """
        Update RazorpayX Payout Status in Payment Entry.

        To trigger notification on change of status.

        :param status: Payout Webhook Status.
        """

        if not status or status not in PAYOUT_STATUS.values():
            return

        if status == self.get_pe_rpx_status():
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

    def handle_failure(self):
        """
        Handle the Payout Failure.

        - Cancel the Payment Entry.
        - Cancel Fees and Tax JE if available.
        - Cancel the Payout Link if the payout is made from the Payout Link.
        """
        if not self.status or not is_payout_failed(self.status):
            return

        self.cancel_payment_entry()
        self.cancel_fees_and_tax_je()
        self.cancel_payout_link()

    def create_journal_entry_for_fees(self):
        """
        Create a Journal Entry for the Payout Charges (fees + tax).

        Reference: https://razorpay.com/docs/x/manage-teams/billing/
        """

        def get_credit_account(fees_config: dict) -> str:
            if fees_config.payouts_from == PAYOUT_FROM.RAZORPAYX_LITE.value:
                return frappe.db.get_value(
                    "Bank Account", self.source_doc.bank_account, "account"
                )

            return fees_config.payable_account

        if (
            not self.source_doc
            or not self.id
            or self.status
            not in [
                PAYOUT_STATUS.PROCESSED.value,
                PAYOUT_STATUS.PROCESSING.value,
            ]
        ):
            return

        fees = self.payload_entity.get("fees") or 0
        # !Note: fees is inclusive of tax and it is in paisa
        # Example: fees = 236 (2.36 INR) and tax = 36 (0.36 INR) => Charge = 200 (2 INR) | Tax = 36 (0.36 INR)

        # conditions to create JE
        if not fees or PayoutWebhook.je_exists(self.id):
            return

        fees_config = get_fees_accounting_config(self.config_name)

        if not fees_config.automate_fees_accounting:
            return

        if (
            fees_config.payouts_from == PAYOUT_FROM.RAZORPAYX_LITE.value
            and self.status != PAYOUT_STATUS.PROCESSING.value
        ):
            return

        if (
            fees_config.payouts_from == PAYOUT_FROM.CURRENT_ACCOUNT.value
            and self.status != PAYOUT_STATUS.PROCESSED.value
        ):
            return

        fees = paisa_to_rupees(fees)

        self.create_je(
            accounts=[
                {
                    "account": fees_config.creditors_account,
                    "party_type": "Supplier",
                    "party": fees_config.supplier,
                    "debit_in_account_currency": fees,
                    "credit_in_account_currency": 0,
                },
                {
                    "account": get_credit_account(fees_config),
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": fees,
                },
            ],
            user_remark=self.get_je_remark(fees),
            cheque_no=self.id,
        )

    def cancel_fees_and_tax_je(self):
        if not self.id:
            return

        je = frappe.get_doc(
            "Journal Entry",
            {"cheque_no": self.id, "reversal_of": ["is", "not set"], "docstatus": 1},
        )

        if je:
            je.cancel()

    ### UTILITIES ###
    # static methods
    def fmt_inr(amount: int) -> str:
        return fmt_money(amount, currency=PAYOUT_CURRENCY.INR.value)

    def je_exists(
        cheque_no: str, reversal_of: Literal["set", "not set"] = "not set"
    ) -> str | None:
        return frappe.db.exists(
            "Journal Entry",
            {
                "cheque_no": cheque_no,
                "reversal_of": ["is", reversal_of],
            },
        )

    # instance methods
    def get_posting_date(self):
        if created_at := self.payload_entity.get("created_at"):
            return get_epoch_date(created_at)

        return today()

    def get_je_remark(self, fees: int | None = None, reversal: bool = False) -> str:
        user_remark = ""

        if self.source_doc:
            user_remark = (
                f"{self.source_doc.doctype}: {self.get_source_formlink(True)}\n"
            )

        if reversal:
            user_remark += f"Reversal ID: {self.reversal_id}"
        else:
            user_remark += f"Payout ID: {self.id}"

        if self.status:
            user_remark += f"\nPayout Status: {self.status.title()}"

        if fees:
            if fee_type := self.payload_entity.get("fee_type"):
                user_remark += f"\nFee Type: {fee_type}"

            tax = paisa_to_rupees(self.payload_entity.get("tax") or 0)
            user_remark += f"\nFees: {PayoutWebhook.fmt_inr(fees - tax)} | Tax: {PayoutWebhook.fmt_inr(tax)}"

        user_remark += f"\n\nIntegration Request: {self.get_ir_formlink(True)}"

        return user_remark

    def set_id_field(self) -> str:
        field_mapper = {
            EVENTS_TYPE.PAYOUT.value: "razorpayx_payout_id",
            EVENTS_TYPE.TRANSACTION.value: "razorpayx_payout_id",
            EVENTS_TYPE.PAYOUT_LINK.value: "razorpayx_payout_link_id",
        }

        self.id_field = field_mapper.get(self.event_type) or "razorpayx_payout_id"

    def create_je(self, **kwargs):
        je = frappe.new_doc("Journal Entry")
        je.update(
            {
                "voucher_type": "Journal Entry",
                "is_system_generated": 1,
                "company": self.source_doc.company,
                "posting_date": self.get_posting_date(),
                **kwargs,
            }
        )

        je.flags.skip_remarks_creation = True
        je.submit()

        return je

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

        self.order_maintained = bool(
            self.status
            and PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[self.get_pe_rpx_status()]
        )

        return self.order_maintained

    def get_pe_rpx_status(self) -> str:
        """
        Get the Payment Entry's RazorpayX Payout Status.
        """
        return self.source_doc.razorpayx_payout_status.lower()

    def get_updated_reference(self) -> dict:
        """
        Get PE's `reference_no` and `remarks` based on the UTR.
        """

        if not self.utr:
            return {}

        return {
            "reference_no": self.utr,
            "remarks": self.source_doc.remarks.replace(
                self.source_doc.reference_no, self.utr, 1
            ),
        }

    ### CANCELLATION ###
    def cancel_payout_link(self) -> bool:
        """
        Cancel the Payout Link if the Payout is made from the Payout Link.
        """
        # TODO: Need to check what is exact behaviour of the Payout Link on the failure of payout!
        link_id = self.source_doc.razorpayx_payout_link_id

        if not link_id:
            return

        try:
            payout_link = RazorpayXLinkPayout(self.config_name)
            status = payout_link.get_by_id(link_id, "status")

            if is_payout_link_failed(status):
                return

            if status == PAYOUT_LINK_STATUS.ISSUED.value:
                payout_link.cancel(
                    link_id,
                    source_doctype=self.source_doctype,
                    source_docname=self.source_docname,
                )

        # TODO: should update IR status to `Failed`
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
        if self.source_doc.docstatus != 1:
            return

        self.source_doc.flags.__canceled_by_rpx = True
        self.source_doc.cancel()


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

    def handle_failure(self):
        """
        Handle the Payout Link Failure.

        - Update thr Payout Status to `Cancelled`.
        - Cancel the Payment Entry.
        """
        if not self.status or not is_payout_link_failed(self.status):
            return

        self.update_payout_status(PAYOUT_STATUS.CANCELLED.value)
        self.cancel_payment_entry()

    ### UTILITIES ###
    def is_order_maintained(self) -> bool:
        """
        Check if the order maintained or not.

        Caution: ⚠️ Payout link status is not maintained in the Payment Entry.
        """
        self.order_maintained = bool(self.status)

        return self.order_maintained


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
        self.transaction_id = self.payload_entity["id"]

        if not self.payload_entity:
            return

        self.transaction_source = self.payload_entity.get("source") or {}

        if not self.transaction_source:
            return

        self.transaction_type = self.transaction_source.get("entity")
        self.utr = self.transaction_source.get("utr")
        self.status = self.transaction_source.get("status")
        self.notes = self.transaction_source.get("notes") or {}

        if self.transaction_type == TRANSACTION_TYPE.PAYOUT.value:
            self.id = self.transaction_source.get("id")
            self.status = self.transaction_source.get("status")
        elif self.transaction_type == TRANSACTION_TYPE.REVERSAL.value:
            self.reversal_id = self.transaction_source.get("id")
            self.id = self.transaction_source.get("payout_id")
            self.status = PAYOUT_STATUS.REVERSED.value

    ### APIs ###
    def process_webhook(self, *args, **kwargs):
        """
        Process RazorpayX Payout Related Webhooks.
        """
        self.update_payment_entry()

        if not self.order_maintained:
            return

        self.set_utr_in_bank_transaction()
        self.handle_payout_reversal()

    def handle_failure(self):
        pass

    def set_utr_in_bank_transaction(self):
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

    def handle_payout_reversal(self):
        if not self.source_doc or self.status != PAYOUT_STATUS.REVERSED.value:
            return

        self.cancel_payout_link()

        if not is_create_je_on_reversal_enabled(self.config_name):
            return

        # to create JE
        self.total_allocated_amount = self.source_doc.total_allocated_amount or 0
        self.unallocated_amount = self.source_doc.unallocated_amount or 0

        self.unreconcile_payment_entry()
        self.create_payout_reversal_je()
        self.reverse_fees_and_tax_je()

    def unreconcile_payment_entry(self):
        vouchers = []

        source = {
            "company": self.source_doc.company,
            "voucher_type": self.source_doc.doctype,
            "voucher_no": self.source_doc.name,
        }

        for d in self.source_doc.references:
            vouchers.append(
                {
                    **source,
                    "against_voucher_type": d.reference_doctype,
                    "against_voucher_no": d.reference_name,
                }
            )

        if not vouchers:
            return

        create_unreconcile_doc_for_selection(json.dumps(vouchers))

    def create_payout_reversal_je(self):
        if PayoutWebhook.je_exists(self.reversal_id):
            return

        accounts = [
            {
                "account": self.source_doc.paid_to,
                "party_type": self.source_doc.party_type,
                "party": self.source_doc.party,
                "credit_in_account_currency": (
                    self.total_allocated_amount + self.unallocated_amount
                ),
                "debit_in_account_currency": 0,
                "reference_type": self.source_doc.doctype,
                "reference_name": self.source_doc.name,
            },
            {
                "account": self.source_doc.paid_from,
                "debit_in_account_currency": self.source_doc.paid_amount,
                "credit_in_account_currency": 0,
            },
        ]

        for deduction in self.source_doc.deductions:
            amount = abs(deduction.amount)
            is_debit = deduction.amount < 0

            account_entry = {
                "account": deduction.account,
                "cost_center": deduction.cost_center,
                "debit_in_account_currency": amount if is_debit else 0,
                "credit_in_account_currency": 0 if is_debit else amount,
            }

            accounts.append(account_entry)

        self.create_je(
            accounts=accounts,
            user_remark=self.get_je_remark(),
            cheque_no=self.reversal_id,
        )

    def reverse_fees_and_tax_je(self):
        fees_je = PayoutWebhook.je_exists(self.id)

        if not fees_je:
            return

        reversal_je = make_reverse_journal_entry(fees_je)
        reversal_je.update(
            {
                "is_system_generated": 1,
                "posting_date": self.get_posting_date(),
                "cheque_no": self.reversal_id,
                "user_remark": f"Integration Request: {self.get_ir_formlink(True)}",
            }
        )
        reversal_je.flags.skip_remarks_creation = True
        reversal_je.submit()

    ### UTILITIES ###
    def should_update_payment_entry(self) -> bool:
        """
        Check if the Payment Entry should be updated or not.

        Note: Source doc (Payment Entry) is set here.
        """
        return bool(self.get_source_doc() and self.is_order_maintained())

    def is_order_maintained(self):
        """
        Check if the order is maintained or not.
        """

        # if status not available, depend on the type
        if not self.status:
            self.order_maintained = self.transaction_type in TRANSACTION_TYPE.values()
        else:
            # if status available, compare with the source doc payout status
            if self.status == PAYOUT_STATUS.REVERSED.value:
                # if status is update via payout's reversed webhook than in transaction webhook reversal will not handled
                self.order_maintained = True
            else:
                self.order_maintained = (
                    PAYOUT_ORDERS[self.status] > PAYOUT_ORDERS[self.get_pe_rpx_status()]
                )

        return self.order_maintained


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
    # EVENTS_TYPE.ACCOUNT.value: AccountWebhook,
}


###### APIs ######
def get_webhook_rate_limit():
    """
    Get the rate limit for the RazorpayX Webhook.
    """

    if authenticate_webhook_request():
        frappe.flags.razorpayx_webhook_authenticated = True
        return 36_00_000

    # failures allowed every hour
    return 10


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=get_webhook_rate_limit, seconds=60 * 60)
def webhook_listener():
    """
    This is the entry point for the RazorpayX Webhook.
    """

    if not frappe.flags.razorpayx_webhook_authenticated:
        return

    payload = frappe.local.form_dict
    payload.pop("cmd")

    event = payload.get("event")
    if is_unsupported_event(event):
        return

    ## Log the webhook request ##
    ir_log = {
        "request_id": frappe.get_request_header("X-Razorpay-Event-Id"),
        "status": "Completed",
        "integration_request_service": f"RazorpayX - {event}",
        "request_headers": dict(frappe.request.headers),
        "data": payload,
        "is_remote_request": True,
    }

    ir = log_integration_request(**ir_log)

    ## Process the webhook ##
    frappe.enqueue(
        process_webhook,
        payload=payload,
        integration_request=ir.name,
    )


def process_webhook(payload: dict, integration_request: str):
    """
    Process the RazorpayX Webhook.

    :param payload: Webhook payload data.
    :param integration_request: Integration Request docname.
    """

    frappe.set_user("Administrator")

    # Getting the webhook processor based on the event type.
    event_type = payload["event"].split(".")[0]  # `event` must exist in the payload
    processor = WEBHOOK_PROCESSORS_MAP[event_type](payload, integration_request)
    processor.process_webhook()


###### UTILITIES ######
def is_unsupported_event(event: str | None) -> bool:
    return bool(not event or event not in SUPPORTED_EVENTS)


def authenticate_webhook_request():
    if not frappe.get_request_header("X-Razorpay-Event-Id"):
        log_webhook_authentication_failure("Event ID Not Found")
        return

    signature = frappe.get_request_header("X-Razorpay-Signature")
    if not signature:
        return

    payload = frappe.local.form_dict
    if not payload.account_id:
        log_webhook_authentication_failure("Account ID Not Found in Payload")
        return

    config = get_razorpayx_config(payload.account_id)
    if not config:
        log_webhook_authentication_failure("RazorpayX Configuration Not Found")
        return

    secret = get_decrypted_password(
        RAZORPAYX_CONFIG, config, "webhook_secret", raise_exception=False
    )
    if not secret:
        log_webhook_authentication_failure("Webhook Secret Not Configured")
        return

    if signature != get_expected_signature(secret):
        log_webhook_authentication_failure("Webhook Signature Mismatch")
        return

    return True


def log_webhook_authentication_failure(reason: str):
    payload = frappe.local.form_dict
    payload.pop("cmd")

    divider = f"\n\n{'-' * 25}\n\n"
    message = f"Reason: {reason}"
    message += divider
    message += (
        f"Request Headers:\n{frappe.as_json(dict(frappe.request.headers), indent=2)}"
    )
    message += divider
    message += f"Request Body:\n{frappe.as_json(payload, indent=2) if payload else frappe.request.data}"

    frappe.log_error(
        title=f"RazorpayX Webhook Authentication Failed: {reason}",
        message=message,
    )


def get_expected_signature(secret: str) -> str:
    return hmac(secret.encode(), frappe.request.data, "sha256").hexdigest()


@frappe.request_cache
def get_razorpayx_config(account_id: str) -> str | None:
    """
    Fetch the RazorpayX Configuration name based on the identifier.

    :param account_id: RazorpayX Account ID (Business ID).
    """

    return frappe.db.get_value(
        doctype=RAZORPAYX_CONFIG,
        filters={
            "account_id": account_id.removeprefix("acc_"),
        },
    )


def get_referenced_docnames(doctype: str, docname: str) -> list[str] | None:
    """
    Get the referenced docnames based.

    - Descending order by creation date.

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


def is_payout_failed(status: str) -> bool:
    """
    Check if the Payout failed (cancelled, failed, rejected) or not.

    :param status: Payout Webhook Status.
    """
    return status in [
        PAYOUT_STATUS.CANCELLED.value,
        PAYOUT_STATUS.FAILED.value,
        PAYOUT_STATUS.REJECTED.value,
    ]


def is_payout_link_failed(status: str) -> bool:
    """
    Check if the Payout Link failed (expired, rejected, cancelled) or not.

    :param status: Payout Link Webhook Status.
    """
    return status in [
        PAYOUT_LINK_STATUS.CANCELLED.value,
        PAYOUT_LINK_STATUS.EXPIRED.value,
        PAYOUT_LINK_STATUS.REJECTED.value,
    ]


# TODO: Handle Fees and Tax deduction at the end of the day
"""
1. Create JE
2. Debit: Creditors Account
3. Credit: Payable Account
3. Amount: Fees + Tax
4. Cheque No: UTR ?
5. User Remark: Fees: 200 | Tax: 36 | Integration Request: IR-00001 (Example)
"""
