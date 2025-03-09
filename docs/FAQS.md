# Frequently Asked Questions (RazorpayX Integration for Frappe/ERPNext)

### 1. Which banks are supported by RazorpayX?  

**Supported Banks:**  
RazorpayX currently supports accounts with **RBL Bank, Yes Bank, IDFC First Bank, and Axis Bank** (the latter is selectively available for enterprise customers).  

**Note:**  

- A **new bank account** is required in most cases (existing accounts may not be compatible).  
- Check [RazorpayX’s official website](https://razorpay.com/x/current-accounts/) for the latest updates, as supported banks may change.  

---

### 2. How do I sign up for RazorpayX?  

**Steps to Sign Up:**  

1. Visit the [RazorpayX portal](https://x.razorpay.com/auth/signup) and sign up.  
2. A RazorpayX representative will contact you to guide you through **documentation requirements**, which vary by business type (e.g., sole proprietorship, LLP, private limited).  
3. The approval process typically takes **7–10 business days** after submitting complete documentation.  

**Pro Tip:** Keep your business PAN, GST, and incorporation documents ready to expedite the process.  

---

### 3. What are the pricing and fees?  

**Special Community Pricing:**  

- **Zero setup fees** or SaaS charges.  
- **Transaction fees** start at **₹1 per payout** (varies by transaction type and volume).  
- **No hidden bank charges** for covered transaction categories (e.g., standard NEFT/IMPS/UPI payouts).  

**Note:**

- Fill out the [Google Form for Discount Pricing](http://bit.ly/3FhJOaA) to get special pricing.
  - A **RazorpayX** representative will contact you with the discounted pricing details.

---

### 4. How do I switch between Test Mode and Live Mode?  

**Steps:**  

1. **In RazorpayX Dashboard:**  
   - Toggle between **Test** (Sandbox) and **Live** modes under *Settings*.  
2. **In ERPNext:**  
   - Navigate to **RazorpayX Configuration** (via the Frappe/ERPNext dashboard).  
   - Ensure the **API Key** and **Secret Key** match the mode (Test/Live) selected in RazorpayX.  

**Important:**  

- Test mode requires sandbox credentials (provided by RazorpayX).  
- Never use live credentials in test mode, or vice versa.  

---

### 5. Can I use multiple RazorpayX accounts?  

**Yes!** Follow these steps:  

1. **Configure Accounts:** Add each RazorpayX account in ERPNext under *Accounts > RazorpayX Configuration*.  
2. **Select During Transactions:** When creating a **Payment Entry**, choose the desired bank account from the *Company Bank Account* dropdown.  

**Note:** Ensure API keys for all accounts are correctly mapped to avoid payout errors.  

---

### Additional Tips  

- **Reconciliation:** Use the *Bank Reconciliation Tool* in ERPNext to sync RazorpayX transactions automatically.  
- **Security:** Rotate API keys quarterly or when team members with access leave.  

---

**Still Have Questions?**  
Visit [RazorpayX Documentation](https://razorpay.com/docs/x/) or connect with their support representative.  
