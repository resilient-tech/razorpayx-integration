from razorpayx_integration.payment_utils.constants.enums import BaseEnum


class TRANSFER_METHOD(BaseEnum):
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    LINK = "Link"
