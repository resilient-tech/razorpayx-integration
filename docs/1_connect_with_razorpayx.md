# 🚀 Connect ERPNext with RazorpayX

## 📝 Step 1: Create a Company Bank Account with RazorpayX Details

### Mandatory Fields

- **Is Company Account**: Enable this option.
- **Bank Account No.**: Add your RazorpayX account details.

![1-Bank Account](https://github.com/user-attachments/assets/39ffad44-b626-4511-a827-b48dbf61beb5)

### For Test Mode

- **Bank Account No.**: Use the **Customer Identifier** from your RazorpayX account. [Get it here](https://x.razorpay.com/settings/banking).  
  
  ![2-Customer-Identifier](https://github.com/user-attachments/assets/3fb18b86-15d6-4c3f-a440-6163c80c4408)

### For Live Mode

- **Bank Account No.**: Use your **Current Account Number** or **Customer Identifier**.  
  ![3-bank_account_no_type](https://github.com/user-attachments/assets/86a992c6-f30b-4ef3-91e3-264b92b6d4f8)

---

## ⚙️ Step 2: Create a RazorpayX Configuration

![image](https://github.com/user-attachments/assets/c19b2c10-7245-4149-ba9b-f03a5eb72326)


### Get API Credentials

- **API Key** and **API Secret**: If not available, generate them from [here](https://x.razorpay.com/settings/developer-controls).  
  ![5-API key and Secret](https://github.com/user-attachments/assets/69088c51-a6ec-45d2-877d-17f7f73f636c)

- **Account ID**: Retrieve it from [here](https://x.razorpay.com/settings/business) (It’s your **Business ID**).  
  ![6-Account ID](https://github.com/user-attachments/assets/9481d9a3-47cc-41f6-9ee4-5afa45a38b93)

**Note:** You can create multiple settings with different bank accounts associated with RazorpayX.

---

### 🌐 Set Up Webhooks

1. **Copy Webhook URL**: Click the `Copy Webhook URL` button in the RazorpayX Configuration.
   ![image](https://github.com/user-attachments/assets/a72f619e-bbbe-40e2-a7e4-d527c66baa66)

3. **Add Webhook URL to RazorpayX Dashboard**: Paste the URL [here](https://x.razorpay.com/settings/developer-controls).  
   ![7-webhook](https://github.com/user-attachments/assets/72b9657c-00d5-4e84-a829-a74d323eff8a)

   **For Local Testing**: Refer to [this guide](https://discuss.frappe.io/t/guide-for-using-ngrok-for-webhook-testing/141902).

4. **Supported Webhooks (12 Events)**:

   ```shell
   # Payout
   - payout.pending
   - payout.rejected
   - payout.queued
   - payout.initiated
   - payout.processed
   - payout.reversed
   - payout.failed
   - payout.updated
   # Payout Link
   - payout_link.cancelled
   - payout_link.rejected
   - payout_link.expired
   # Transaction
   - transaction.created
   ```

   For more details, visit [RazorpayX Webhook Events](https://razorpay.com/docs/x/apis/subscribe/#webhook-events-and-descriptions).

5. **Add Webhook Secret**: Ensure you add the webhook secret; otherwise, ERPNext won’t receive updates.

---

## 🤖 Step 3: Configure Automation

### 1. **Pay on Auto Submit**

- **Checked** ☑️ by default.
- If a `Payment Entry` is submitted via automation or server-side processes, the payout will be made if `Make Online Payment` is checked in the Payment Entry (PE).
- If unchecked and the PE is submitted with the `initiated_by_payment_processor` flag, the payout will not be made, and `Make Online Payment` will be unchecked.

### 2. **Automatically Cancel Payout on Payment Entry Cancellation**

- If checked, the payout and payout link will be canceled automatically upon PE cancellation (helpful for bulk cancellations).
- If unchecked, a confirmation dialog will appear for single PE cancellations if the payout or payout link is cancellable.

---

## 🔄 Sync Transactions

Sync bank transactions with ERPNext using the RazorpayX API.

![image](https://github.com/user-attachments/assets/af2bc661-488c-4d47-89f5-fa8c1164c952)

![image](https://github.com/user-attachments/assets/f65e4ae9-e8fc-4fa5-b25f-de4342732dde)
