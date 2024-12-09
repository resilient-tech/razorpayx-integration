import frappe
from frappe.query_builder import Case

from razorpayx_integration.razorpayx_integration.constants import (
    RAZORPAYX_SETTING_DOCTYPE,
)


def execute():
    """
    Create Payment Entries to all Payable Account via RazorpayX.
    """

    # ? Payment Entries will create everyday ?
    # ? If PE is already created for Invoice/Party how to handle it ?
    # ? How to determine amount ?
    # ? When creating PE, which mode to use ?
    # ? If `Automatic Payments` is enabled, then what mode to use ?

    settings = get_razorpayx_settings()

    if not settings:
        return

    # get data to create payment entries
    payment_entries = []

    for setting in settings:
        if entry := get_payable_data(setting):
            payment_entries.extend(entry)

    if not payment_entries:
        return

    # create payment entries
    for entry in payment_entries:
        create_payment_entry(entry)


def get_razorpayx_settings() -> list[dict] | None:
    """
    Get RazorpayX Setting for Payment Entry generation.
    """
    RIS = frappe.qb.DocType(RAZORPAYX_SETTING_DOCTYPE)

    payment_mode = (
        Case()
        .when(RIS.enable_automatic_payments == 1, RIS.manual_mode)
        .else_(RIS.automatic_mode)
        .as_("payment_mode")
    )

    query = (
        frappe.qb.from_(RIS)
        .select(
            RIS.name.as_("razorpayx_account"),
            RIS.company,
            payment_mode,
            RIS.payouts_by,
            RIS.order_to_pay,
            # TODO: Add more fields
        )
        .where(RIS.disabled == 0)
        .where(RIS.auto_generate_entries == 1)
    )

    return query.run(as_dict=1)


def get_payable_data(setting: dict) -> list[dict] | None:
    """
    1. Get payable accounts and amounts.
    2. Fetch by `payouts_by` and `order_to_pay`.
    3. Return the as `Payment Entry` data.

    - Note:
        - If `payouts_by` is `By Invoice`, then single reference to `Invoice`.
        - If `payouts_by` is `By Party`, then multiple references to `Party`.
    """
    pass


def create_payment_entry(entry: dict):
    """
    Create Payment Entry based on the payable data.
    """
    pass
