# 🚀 Connect ERPNext with RazorpayX

## 📝 Step 1: Create a Company Bank Account with RazorpayX Details

If you already have a bank account configured, you can skip this step.

### Mandatory Fields

- **Is Company Account**: Enable this option.  
- **Bank Account No.**: Add your bank account number associated with RazorpayX.  

![ERPNext Bank Account Doc](https://github.com/user-attachments/assets/78267bd9-6705-472d-a066-d42a5d170031)

### For Test Mode

- **Bank Account No.**: Use the **Customer Identifier** from your RazorpayX account. [Get it from here](https://x.razorpay.com/settings/banking).  

  ![Customer Identifier](https://github.com/user-attachments/assets/9d03d92f-7ca7-4dc9-9641-5f6263d90362)

### For Live/Production Mode

- **Bank Account No.**: Use your **Current Account Number** or **Customer Identifier** as per your requirement.  
  ![Bank Account No. Type](https://github.com/user-attachments/assets/86a992c6-f30b-4ef3-91e3-264b92b6d4f8)

## ⚙️ Step 2: Create a RazorpayX Configuration

1. In your ERPNext site, search for `RazorpayX Configuration` in the search bar and open the list view.  
2. Add a new configuration.  

![RazorpayX Configuration Document](https://github.com/user-attachments/assets/f240a344-80e0-4c77-81e2-ef67a7c105f8)

### Get API Credentials

- **API Key** and **API Secret**:  
  - If not available, [generate them from here](https://x.razorpay.com/settings/developer-controls).  
  - **Note**: For first-time generation, a direct button is available to create the `KEY` and `SECRET`.  

  ![Key ID and Secret Generation](https://github.com/user-attachments/assets/ddfc1b0d-24f2-4213-89fd-dbe7ce40fab1)

- **Account ID**:  
  - This is your **Business ID** provided by RazorpayX. [Get it from here](https://x.razorpay.com/settings/business).  

  ![Account ID](https://github.com/user-attachments/assets/d13001a2-a128-4d91-99ee-07ff08a4c56d)


### 🌐 Set Up Webhooks

Webhooks are used for real-time payout status updates.

1. **Copy Webhook URL**: Click the `Copy Webhook URL` button in the RazorpayX Configuration.  
  ![Copy Webhook URL](https://github.com/user-attachments/assets/c5dbba85-9289-4031-ae63-efaa647d3852)

2. **Add Webhook URL to RazorpayX Dashboard**: Paste the URL [here](https://x.razorpay.com/settings/developer-controls).  
  ![RazorpayX Dashboard for Webhook](https://github.com/user-attachments/assets/08d25a69-87c2-46f7-95d4-27a5c30d4f75)

   - **Note**: Only enable supported webhooks.  

3. **Supported Webhooks (11 Events)**:

   ```shell
   # Payout
   - payout.pending
   - payout.rejected
   - payout.queued
   - payout.initiated
   - payout.processed
   - payout.reversed
   - payout.failed
   # Payout Link
   - payout_link.cancelled
   - payout_link.rejected
   - payout_link.expired
   # Transaction
   - transaction.created
   ```

   For more details, visit [RazorpayX Webhook Events](https://razorpay.com/docs/x/apis/subscribe/#webhook-events-and-descriptions).

4. **Add Webhook Secret**: Ensure you add the webhook secret; otherwise, ERPNext won’t receive updates.  
   - A strong webhook secret is recommended for enhanced security.  

**Note**:  

- Test and Live modes require different **API Keys** and **Webhook URLs**.  
- For more details on Test and Live modes, [visit here](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/setup/1_setup_test_and_live_mode.md).  

### 🏦 Set Company Bank Account

- Set the bank account that is associated with RazorpayX.  

### 🤖 Configure Automation

1. **Automatically Cancel Payout on Payment Entry Cancellation**
   - If checked, the payout and payout link will be canceled automatically upon Payment Entry cancellation (helpful for bulk cancellations).  
   - If unchecked, a confirmation dialog will appear for single Payment Entry cancellations if the payout or payout link is cancellable.  
   - See [Cancellation Workflow](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/payout/5_cancel_payout.md) for more details.  

2. **Pay on Auto Submit**
   - This feature is only available if the [Payments Processor](https://github.com/resilient-tech/payments-processor) app is installed.  
   - **Checked** ☑️ by default.  
   - If a `Payment Entry` is submitted via automation, the payout will be made if `Make Online Payment` is checked in the Payment Entry.  
   - If unchecked and the Payment Entry is submitted with the `initiated_by_payment_processor` flag, the payout will not be made, and `Make Online Payment` will be unchecked.  
   - ![Pay On Auto Submit](https://github.com/user-attachments/assets/cf204193-cf55-4715-a9e7-770fa3937dc0)

### 🤖  Accounting

- For detailed information, see [Accounting with RazorpayX Integration](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/accounting).

---

### Multiple configurations with different bank accounts for the same company associated with RazorpayX are allowed.