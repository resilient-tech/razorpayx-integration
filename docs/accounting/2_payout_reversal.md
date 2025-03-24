# 🔄 Payout Reversal Accounting

![Configuration Image](https://github.com/user-attachments/assets/1a37825e-ca0c-4a9c-ae20-ff6239f551a0)

## ⚙️ Configuration Fields

### 1. **Create JE on Payout Reversal**

- **Enabled by default** (`Checked`).  
- If enabled:  
  - Unreconcile the **Payment Entry** from which the payout was initiated.  
  - Create a **Reversal Journal Entry** for the Payment Entry, respecting its ledger.  
  - Reverse the **Fees Journal Entry** (if applicable).  

## 🔄 Journal Entry (JE) Creation Process

### **Payout Reversal JE**

- Deductions are also reversed if applicable.  
- Deductions/Losses are handled automatically in the reversal JE.  

**Payment Entry**:  
![Payment Entry](https://github.com/user-attachments/assets/38ea7162-1385-442e-8e5a-7438421c2df5)  

**Accounting Ledger of Payment Entry**:  
![Accounting Ledger of Payment Entry](https://github.com/user-attachments/assets/f416286c-11f0-4be6-bbbf-2a19c51d872b)  

**Reversal JE**:  
![Reversal JE](https://github.com/user-attachments/assets/368ce82d-bad2-4514-96b2-2c5f30168025)  

### **Fees Reversal JE**

- If fees were deducted during the original payout, a **Fees Reversal JE** is created to reverse the fees.  

![Fees Reversal JE](https://github.com/user-attachments/assets/0feeb6b9-15fc-4877-a3c9-352ce4d57d1f)  

### **Bank Transaction**

- For reconciliation, both reversal JEs are used for the **Deposit** (credit) of the reversed amount.  
  - If the payout was made from **RazorpayX Lite**, the **Fees Reversal JE** will be referenced.  
  - Otherwise, only the **Payout Reversal JE** will be referenced.  

![Bank Transaction](https://github.com/user-attachments/assets/d4baa18d-027e-42d1-b5f0-a1fe1232da32)  
