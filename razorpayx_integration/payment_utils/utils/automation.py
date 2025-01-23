# TODO: create PE
# TODO: Pay via RazorPayX on submit


def autocreate_payment_entry():
    pass


# at the middle of the day
def autosubmit_payment_entry():
    # identify flagged invoices
    # within threshold?
    # pay with flag
    pass


# at the start of the day
def determine_invoices_to_pay():
    # Create a flag in Payment Entry that it's auto-generated
    # return invoices with amount
    # email to auto-payment manager
    pass


def is_blocked_invoice(pinv):
    pass


def is_blocked_customer(supplier):
    pass


def withold_part_payment(pinv):
    pass


def create_payment_entry():
    # pe.run_method("set_payment_information") in razorpayx
    pass
