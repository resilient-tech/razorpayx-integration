# 💳 Make RazorpayX Payout with Payment Entry

## 📋 Prerequisites

- Ensure all [Payout Requirements](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/payout/1_requirements.md) are met.  
- Complete the [Authentication Setup](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/payout/2_Authentication.md) for secure transactions.  

## 🚀 Make Payout on Payment Entry Submission

1. Create a **Payment Entry** with the following details:  
   - **Payment Type**: Pay  
   - **Company Bank Account**: Linked to RazorpayX Configuration  
   - **Paid from Account Currency**: INR  
   - **Make Online Payment**: Check this option to initiate the payout on submission.  

2. Submit the Payment Entry to trigger the payout via `Pay and Submit`  

https://github.com/user-attachments/assets/3f8679af-af6d-4edb-8ae1-a0a26576061d

**Note**:

- If a **Workflow** is active for the Payment Entry, the `Pay and Submit` button will not be available, and `Make Online Payment` will be unchecked if previously checked.  

## ⏳ Make Payout After Payment Entry Submission

- If the Payment Entry is submitted without checking `Make Online Payment`, user can still initiate the payout manually.  
- A custom button, **Make Payout**, will be available if the Company's Bank Account is valid and linked to RazorpayX.  

https://github.com/user-attachments/assets/53b18844-88aa-403d-aad3-c07478a76a51

## 📦 Bulk Payout

1. Select multiple **Payment Entries** in **Draft** status with valid payout information.  
2. Use the **Pay and Submit** bulk action to initiate payouts for all selected entries.  
   - **Make Online Payment** is optional and can be marked during the bulk action.  

**Recommendations for Bulk Payouts**:

- Ensure each Payment Entry has valid:  
  - **Company Bank Account**  
  - **Party Bank Account**  
  - **Payment Transfer Method**  
  - **Contact Details** (if using **Link** for payment).

- If a **Party Bank Account** is selected, the payout will be made via **NEFT** by default. Otherwise, it will be made via **Link**.  

https://github.com/user-attachments/assets/5cf6cb2d-3e06-4042-8295-68caae710050

**Note:** A maximum of 500 Payment Entries are supported for bulk payouts.
