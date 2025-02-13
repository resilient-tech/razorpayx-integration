from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class TRANSFER_METHOD(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "Link"


BANK_METHODS = [
    TRANSFER_METHOD.NEFT.value,
    TRANSFER_METHOD.RTGS.value,
    TRANSFER_METHOD.IMPS.value,
]

BANK_ACCOUNT_REQD_METHODS = [*BANK_METHODS, TRANSFER_METHOD.UPI.value]
