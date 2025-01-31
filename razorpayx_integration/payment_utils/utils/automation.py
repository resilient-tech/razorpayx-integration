# TODO: create PE
# TODO: Pay via RazorPayX on submit

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
from pypika import Order


def autocreate_payment_entry():
    # get bank accounts with auto generate enabled and determine company from this
    # get all purchase invoices with outstanding amount > 0
    # group invoices by supplier and create a payment entry subject to a max of outstanding amount
    # get suppliers without blocked auto payment
    # get supplier outstanding amounts

    # TODO: ERPNext PR for blocked invocie
    pass


# at the middle of the day
def autosubmit_payment_entry():
    settings = frappe._dict(
        frappe.get_all(
            "Auto Payment Settings",
            filters={"disabled": 0, "auto_submit_entries": 1},
            fields=["bank_account", "payment_threshold"],
            as_list=True,
        )
    )

    if not settings:
        return

    entries = frappe.get_all(
        "Payment Entry",
        filters={"docstatus": 0, "is_auto_generated": 1},
        fields=["name", "bank_account", "paid_amount"],
    )
    # TODO: handle supplier config
    frappe.flags.authenticated_by_cron_job = True

    for entry in entries:
        setting = settings.get(entry.bank_account)
        if setting and entry.paid_amount > setting.payment_threshold:
            continue

        pe = frappe.get_doc("Payment Entry", entry.name)
        pe.submit()


# at the start of the day
def determine_invoices_to_pay():
    # return invoices with amount
    # email to auto-payment manager
    pass


def create_payment_entry():
    # pe.run_method("set_payment_information") in razorpayx
    pass


def process_payments():
    auto_pay_settings = frappe.get_all("Auto Payment Settings", "*", {"disabled": 0})
    for setting in auto_pay_settings:
        PaymentsProcessor(setting)


class PaymentsProcessor:
    def __init__(self, setting):
        self.setting = setting
        self.next_payment_date = "2025-01-31"  # TODO based on next payment date

        self.get_invoices()
        self.get_suppliers()
        self.process_invoices()

        for supplier in self.suppliers.values():
            if not supplier.invoices:
                continue

            for invoice_list in supplier.invoices.values():
                self.make_payments(supplier, invoice_list)

    def get_invoices(self):
        """
        Get all due invoices

        eg:

        self.invoices = {
            "PI-00001": {
                "supplier": "Supplier Name",
                "outstanding_amount": 1000,
                "total_outstanding_due": 1000,  # after adjusting paid amount
                "payment_terms": [
                    {
                        "due_date": "2025-01-31",
                        "outstanding_amount": 1000, # after adjusting paid amount
                        "discount_date": "2025-01-31",
                        "discount_type": "Percentage",
                        "discount_percentage": 5,
                        "discount_amount": 50,
                    }
                ]
                ...
            }
            ...
        }
        """
        doc = frappe.qb.DocType("Purchase Invoice")
        terms = frappe.qb.DocType("Payment Schedule")
        invoices = (
            frappe.qb.from_(doc)
            .join(terms)
            .on((doc.name == terms.parent) & (terms.parenttype == "Purchase Invoice"))
            .select(
                doc.name,
                doc.supplier,
                doc.outstanding_amount,
                doc.grand_total,
                doc.rounded_total,
                doc.currency,
                doc.contact_person,
                doc.bill_no,
                doc.is_return,
                doc.on_hold,
                doc.hold_comment,
                doc.release_date,
                terms.due_date.as_("term_due_date"),
                # TODO: check if this amount is correct
                terms.outstanding.as_("term_outstanding_amount"),
                terms.discount_date.as_("term_discount_date"),
                terms.discount_type.as_("term_discount_type"),
                terms.discount.as_("term_discount"),
            )
            .where(
                doc.docstatus == 1,
                doc.outstanding_amount != 0,
                doc.company == self.setting.company,
            )
            .where(  # invoice is due
                (doc.is_return == 1)  # immediately claim refund for returns
                | ((doc.is_return == 0) & (terms.due_date < self.next_payment_date))
                | (
                    (doc.is_return == 0)
                    & (terms.discount_date.notnull())
                    & (terms.discount_date < self.next_payment_date)
                )
            )
            .orderby(terms.due_date, order=Order.asc)
            .run(as_dict=True)
        )

        self.invoices = frappe._dict()

        for row in invoices:
            if not self.is_invoice_due(row):
                continue

            invoice_total = row.rounded_total or row.grand_total
            paid_amount = invoice_total - row.outstanding_amount

            payment_term = frappe._dict(
                {
                    "due_date": row.pop("term_due_date"),
                    "outstanding_amount": row.pop("term_outstanding_amount"),
                    "discount_date": row.pop("term_discount_date"),
                    "discount_type": row.pop("term_discount_type"),
                    "discount": row.pop("term_discount"),
                }
            )

            updated = self.invoices.setdefault(
                row.name, frappe._dict({**row, "total_outstanding_due": -paid_amount})
            )

            # update total outstanding due based on paid amount
            term_outstanding = payment_term.outstanding_amount

            if updated.total_outstanding_due < 0:
                payment_term.outstanding_amount = max(
                    0, term_outstanding + updated.total_outstanding_due
                )

            self.apply_discount(payment_term)

            updated.total_outstanding_due += term_outstanding
            updated.setdefault("payment_terms", []).append(payment_term)

        # self.processed_invoices = self.process_invoices()

        # for fn in frappe.get_hooks("filter_auto_payment_invoices"):
        #     frappe.get_attr(fn)(invoices=self.processed_invoices)

    def get_suppliers(self):
        suppliers = frappe.get_all(
            "Supplier",
            filters={
                "name": ("in", {invoice.supplier for invoice in self.invoices}),
            },
            fields=(
                "name",
                "disabled",
                "on_hold",
                "hold_type",
                "release_date",
                "disable_auto_generate_payment_entry",
            ),
        )

        self.suppliers = {supplier.name: supplier for supplier in suppliers}

    def process_invoices(self):
        self.processed_invoices = frappe._dict()

        invalid = self.processed_invoices.setdefault("invalid", frappe._dict())
        valid = self.processed_invoices.setdefault("valid", frappe._dict())

        for invoice in self.invoices.values():
            supplier = self.suppliers.get(invoice.supplier)

            # supplier validations
            if not supplier:
                _invoice = {
                    **invoice,
                    "reason": "Supplier not found",
                    "reason_code": "1000",
                }

                invalid.setdefault(invoice.supplier, []).append(_invoice)
                continue

            if msg := self.is_supplier_disabled(supplier):
                invalid.setdefault(invoice.supplier, []).append({**invoice, **msg})
                continue

            if msg := self.is_supplier_blocked(supplier):
                invalid.setdefault(invoice.supplier, []).append({**invoice, **msg})
                continue

            if msg := self.is_auto_generate_disabled(supplier):
                invalid.setdefault(invoice.supplier, []).append({**invoice, **msg})
                continue

            if msg := self.payment_entry_exists(supplier):
                invalid.setdefault(invoice.supplier, []).append({**invoice, **msg})
                continue

            # invoice validations
            if msg := self.is_invoice_blocked(invoice):
                invalid.setdefault(invoice.supplier, []).append({**invoice, **msg})
                continue

            valid.setdefault(invoice.supplier, []).append(invoice)

        # Exclude foreign currency invoices
        # Use Early Payment Discount
        # check payment terms for the complete invoice

        pass

    def is_invoice_due(self, invoice):
        if invoice.is_return:
            return True

        if (
            self.setting.claim_early_payment_discount
            and invoice.term_discount_date
            and invoice.term_discount_date < self.next_payment_date
        ):
            return True

        if invoice.term_due_date and invoice.term_due_date < self.next_payment_date:
            return True

        return False

    def apply_discount(self, payment_term):
        if not (
            self.setting.claim_early_payment_discount
            and payment_term.discount_date
            and payment_term.discount_date < self.next_payment_date
        ):
            payment_term.discount_amount = 0
            return

        if payment_term.discount_type == "Percentage":
            payment_term.discount_amount = (
                payment_term.outstanding_amount * payment_term.discount / 100
            )
        else:
            payment_term.discount_amount = payment_term.discount

    def is_supplier_disabled(self, supplier):
        if not supplier.disabled:
            return False

        return {
            "reason": "Supplier is disabled",
            "reason_code": "1001",
        }

    def is_supplier_blocked(self, supplier):
        if not supplier.on_hold:
            return False

        if supplier.hold_type not in ["All", "Payments"]:
            return False

        if supplier.release_date and supplier.release_date > today():
            return False

        return {
            "reason": "Payments to supplier are blocked",
            "reason_code": "1002",
        }

    def is_auto_generate_disabled(self, supplier):
        if not supplier.disable_auto_generate_payment_entry:
            return False

        return {
            "reason": "Auto generate payment entry is disabled for this supplier",
            "reason_code": "1003",
        }

    def payment_entry_exists(self, supplier):
        if self.draft_payment_parties is None:
            # TODO: Should we check if draft is for a specific invoice instead?
            self.draft_payment_parties = frappe.get_all(
                "Payment Entry",
                filters={
                    "docstatus": 0,
                    "payment_type": "Pay",
                    "party_type": "Supplier",
                    "party": ["in", self.suppliers.keys()],
                },
                pluck="party",
            )

        if supplier.name not in self.draft_payment_parties:
            return False

        return {
            "reason": "Draft payment entry already exists for this supplier",
            "reason_code": "1004",
        }

    def is_invoice_blocked(self, invoice):
        if not invoice.on_hold:
            return False

        if invoice.release_date and invoice.release_date > today():
            return False

        return {
            "reason": "Payment for this invoice is blocked",
            "reason_code": "2001",
        }

    def exclude_foreign_currency_invoices(self):
        pass

    def make_payments(self, supplier, invoice_list):
        self.draft_entry = self.autopay_entry = None

        for invoice in invoice_list:
            self.update_payment_entry(supplier, invoice)

        for entry_type in ("draft_entry", "autopay_entry"):
            payment_entry = getattr(self, entry_type)
            if not payment_entry:
                continue

            set_amounts(payment_entry)
            try:
                payment_entry.save()
            except Exception:
                frappe.db.rollback()
                frappe.log_error(
                    title="Error saving automated Payment Entry",
                    message=frappe.get_traceback(),
                )

            frappe.db.commit()

            if entry_type == "draft_entry":
                continue

            try:
                payment_entry.submit()
            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(
                    title="Error submitting automated Payment Entry",
                    message=frappe.get_traceback(),
                )
                payment_entry.db_set("error_message", repr(e))

            frappe.db.commit()

    def update_payment_entry(self, supplier, invoice):
        if self.can_autopay(supplier, invoice):
            if not self.autopay_entry:
                self.autopay_entry = self.create_payment_entry(supplier, invoice)
                self.autopay_entry.pay_on_submit = 1
                return

            payment_entry = self.autopay_entry

        else:
            if not self.draft_entry and not self.get_existing_entry(supplier):
                self.draft_entry = self.create_payment_entry(supplier, invoice)
                return

            payment_entry = self.draft_entry

        payment_entry.append(
            "references",
            {
                "reference_doctype": "Purchase Invoice",
                "reference_name": invoice.name,
                "bill_no": invoice.bill_no,
                "due_date": invoice.due_date,
                "total_amount": invoice.grand_total,
                "outstanding_amount": invoice.outstanding_amount,
                "allocated_amount": invoice.outstanding_amount,
            },
        )

    def create_payment_entry(self, supplier, invoice):
        email_id = frappe.db.get_value(
            "Contact",
            supplier.payment_notification_contact or invoice.contact_person,
            "email_id",
        )

        payment_entry = get_payment_entry("Purchase Invoice", invoice.name)
        payment_entry.update(
            {
                "mode_of_payment": supplier.default_payment_method,
                "contact_person": supplier.payment_notification_contact
                or invoice.contact_person,
                "contact_email": email_id,
                "reference_no": "-",
                "reference_date": today(),
                "paid_from": "",
            }
        )

        company = self.companies[invoice.company]

        if payment_entry.mode_of_payment == "ACH":
            payment_entry.party_bank_account = supplier.default_ach_bank_account
            payment_entry.bank_account = company.default_ach_bank_account
        elif payment_entry.mode_of_payment == "Check":
            payment_entry.bank_account = company.default_check_bank_account

        if payment_entry.bank_account:
            payment_entry.set_bank_account_data()

        return payment_entry
