from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class BANK_PAYMENT_MODE(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "Link"
