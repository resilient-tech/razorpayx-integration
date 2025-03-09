# 🔐 Authentication for Making Payout

## ⚙️ Setup 2FA

1. Go to **System Settings** > **Login** tab.  
2. Scroll down to the **Payment Integration** section.  
3. Set the **Payment Authentication Method**.  
   - Currently, only **OTP App** is available.  
   - In future updates, **SMS** and **Email** will be supported.  
4. Optionally, set up an **OTP Issuer Name** (e.g., Company Name or Site Name).  

![System Settings](https://github.com/user-attachments/assets/eef415a5-b130-456c-913d-efffa669c783)

**Note**: A default **Outgoing Email Account** is required to send emails for authentication.  

## 🔢 OTP Dialog Box

### First-Time OTP Generation

![OTP Dialog Box](https://github.com/user-attachments/assets/93717c2a-9f1e-4459-95ce-32b692f30609)

### Successful OTP App Process (If Already Configured)

![OTP Dialog Box](https://github.com/user-attachments/assets/a66385d2-7208-4d98-ab06-6272877da61b)

## 📧 Sample Emails

### Email for QR Code Link

![Email for Process](https://github.com/user-attachments/assets/f0d799bd-c55b-4d62-8b19-de4419bf82cf)

### After Scanning QR Code

![QR Code Page with Steps](https://github.com/user-attachments/assets/f69729e9-fb43-4a6e-adad-6e0320c64507)

---

## 🔄 Reset Payment OTP Secret

- **Prerequisites**:  
  - The user must have the **Online Payments Authorizer** role.  
  - The **Payment Authentication Method** must be set to **OTP App**.  

- **Steps**:  
  1. Go to **User** > **Password**.  
  2. Click on **Reset Payment OTP Secret**.  

![Reset OTP Secret](https://github.com/user-attachments/assets/a3cb040c-df71-408d-85f8-c03e8a26b7c4)