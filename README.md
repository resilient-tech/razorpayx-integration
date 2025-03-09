<div align="center">

<h1>RazorpayX Integration</h1>

Power your ERPNext payments with RazorpayX – Automate payouts, reconcile transactions, and manage business finances effortlessly

<br><br>

</div>

## 💡 Motivation

Bank integrations in India are usually costly and complex, mainly available to corporate.

We choose RazorpayX because:

- It is a tech layer over traditional bank accounts
- Funds remain secure with a regulated bank
- Onboarding process is hassle-free
- No upfront cost, minimal charges per transaction, transparent pricing
- Robust security

## ✨ Features

- Automated bulk payouts for vendors
- Real-time payment status tracking & transaction reconciliation
- Support for multiple payment modes (IMPS/NEFT/RTGS/UPI)
- Can make payment with Link
- Daily sync bank transactions
- Pre-built templates for workflows and notifications
- Configurable to cater to diverse business processes

**📝 Note:** This integration is designed for **domestic transactions within India 🇮🇳**. Foreign currency transactions are not supported.

## 📈 Why Use This Integration?

- <em>Save Time</em>: Eliminate manual bank transactions from **Net Banking** portals
- <em>Reduce Errors</em>: Auto-sync payment data between ERPNext and Bank
- <em>Financial Control</em>: Approval workflows before initiating payouts
- <em>Secure</em>: Role based access with 2FA to authorize manual payouts

## 📦 Installation

**Prerequisites**

- [ERPNext](https://github.com/frappe/erpnext) Version-15 or above
- [Payment Integration Utils](https://github.com/resilient-tech/payment_integration_utils)
- [Payments Processor](https://github.com/resilient-tech/payments-processor) (optional: to automate workflows) 

Choose one of the following methods to install RazorpayX Integration to your ERPNext site.

<details>
<summary>☁️ Frappe Cloud</summary><br>

Sign up for a [Frappe Cloud](https://frappecloud.com/dashboard/signup?referrer=99df7a8f) free trial, create a new site with Frappe Version-15 or above, and install ERPNext and RazorpayX-Integration from the Apps.

</details>

<details>
<summary>🐳 Docker</summary><br>

Use [this guide](https://github.com/frappe/frappe_docker/blob/main/docs/custom-apps.md) to deploy RazorpayX-Integration by building your custom image.

Sample Apps JSON

```shell
export APPS_JSON='[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/resilient-tech/payment_integration_utils",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/resilient-tech/razorpayx-integration",
    "branch": "version-15"
  }
]'

export APPS_JSON_BASE64=$(echo ${APPS_JSON} | base64 -w 0)
```

</details>

<details>
<summary>⌨️ Manual</summary><br>

Once you've [set up a Frappe site](https://frappeframework.com/docs/v14/user/en/installation/), install app by executing the following commands:

Using Bench CLI

Download the App using the Bench CLI

```sh
bench get-app https://github.com/resilient-tech/payment_integration_utils.git --branch version-15
```

```sh
bench get-app https://github.com/resilient-tech/razorpayx-integration.git --branch version-15
```

Install the App on your site

```sh
bench --site [site name] install-app razorpayx_integration
```

</details>

## 📚 Documentation

1. [Connect ERPNext with RazorpayX](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/1_connect_with_razorpayx.md)
2. [Make payout via RazorpayX within ERPNext](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/2_make_payout.md)
3. [Reconcile Bank Transactions via RazorpayX API](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/3_bank_reconciliation_tool.md)
4. [FAQs](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/docs/4_faqs.md)

🔗 **Google Form for Discount Pricing on RazorpayX Payout Fees**: [Apply Here](http://bit.ly/3FhJOaA)  

## 🤝 Contributing

- [Issue Guidelines](https://github.com/frappe/erpnext/wiki/Issue-Guidelines)
- [Pull Request Requirements](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)

## 📜 License

[GNU General Public License (v3)](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/license.txt)
