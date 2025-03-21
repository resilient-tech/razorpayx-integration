# 💰 Fees and Tax Accounting

![Fees Accounting Fields](https://github.com/user-attachments/assets/1e9ef913-2034-41e7-94d7-8fea9658487b)

For details on charges and deductions, refer to RazorpayX's [Fees and Tax Documentation 🔗](https://razorpay.com/docs/x/manage-teams/billing/).

## ⚙️ Configuration Fields

### 1. Automate Fees Accounting

- **Enabled by default** (`Checked`).
- If enabled, a **Journal Entry (JE)** is created whenever a fee is deducted on a payout.
- If the payout is made from a **Current Account**, the JE is recorded when the payout is **Processed**.
- If the payout is made from **RazorpayX Lite**, the JE is recorded when the payout is in the **Processing** state.

### 2. Payouts from

- Two options are available:
   1. **Current Account**
   2. **RazorpayX Lite**
- If the **Customer Identifier** is entered in the company's bank account details, the payout amount will be deducted from the Lite account.  
- If the **Current Account Number** is entered, the deduction occurs from the Bank's Current Account.  
- For more details, read the [Bank Account Setup Guide](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/setup/2_connect_erpnext_with_razorpayx.md#for-liveproduction-mode).
- By default, **Current Account** is selected.

### 3. Creditors Account

- Used in Journal Entries to **debit the transaction fees**.

![Creditors Account](https://github.com/user-attachments/assets/479d01e2-a704-44cc-896e-ccaaa24d3e6f)

### 4. Supplier

- The **Party and Party Type (Supplier)** associated with the Creditors Account.

### 5. Payable Account

- Used in Journal Entries to **credit the transaction fees**.
- Only applicable when payouts are made from the **Current Account**.

![Payable Account](https://github.com/user-attachments/assets/c34731d1-6745-4dae-86e8-a840a40e2474)

## 🔄 Journal Entry (JE) Creation Process

### 🏦 If Payout is from **Current Account**

- **Creditors Account** ➝ **Debited**  
- **Payable Account** ➝ **Credited**  

**Example Journal Entry**
![JE for Current Account Deduction](https://github.com/user-attachments/assets/d9438c6a-1e65-408a-86d1-567a8c037e51)

📌 **Important Notes:**

- When using the **Current Account**, fees are **not deducted immediately**, but a JE is created to reflect the expected deduction.
- At the end of the day, **RazorpayX deducts the accumulated transaction fees** for all payouts made that day.
- For more details, refer to [Payouts from Current Account](https://razorpay.com/docs/x/manage-teams/billing/#payouts-from-current-account).
- Since this is an anticipated fee deduction, this JE **will not be used for bank reconciliation**.
- When RazorpayX deducts the fees, a final JE is created where:
  - **Payable Account** ➝ **Debited**  
  - **Company Account (COA)** ➝ **Credited**  
  - More details on this will be updated soon...

### 💳 If Payout is from **RazorpayX Lite**

- **Creditors Account** ➝ **Debited**  
- **Company Account (COA)** ➝ **Credited**  

**Company’s RazorpayX Bank Account**
![Company Bank Account](https://github.com/user-attachments/assets/1f81dcb6-da69-4d36-8120-36344a0003e1)

**Company Account**
![Company Account](https://github.com/user-attachments/assets/0d7af968-1eda-4e98-9cfa-15f347909303)

**Example Journal Entry**
![Example JE](https://github.com/user-attachments/assets/d612fd1f-7add-4928-b5db-915c5299b4a6)

📌 **Important Notes:**

- In **RazorpayX Lite**, fees are **deducted immediately when the payout is created**.
- For more details, refer to [Payouts from RazorpayX Lite](https://razorpay.com/docs/x/manage-teams/billing/#payouts-from-razorpayx-lite).
- This JE **will be used for reconciliation** in the Bank Transaction.

**Example Bank Transaction**
![Bank Transaction](https://github.com/user-attachments/assets/48827317-46c4-4a26-a31e-4b1091c2c7db)
