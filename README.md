<div align="center">

<h1>RazorpayX Integration</h1>

Power your ERPNext payments with RazorpayX – Automate payouts, reconcile transactions, and manage business finances effortlessly.
<br><br>

</div>

## 💡 Motivation

Bank integrations in India are usually costly and complex, mainly available to corporates.

We choose RazorpayX because:

- It is a tech layer over traditional bank accounts.
- Funds remain secure with a regulated bank.
- Onboarding process is hassle-free.
- No upfront cost, minimal charges beyond free limits.
- It ensures robust security.

## ✨ Features

- Automated bulk payouts for vendors
- Real-time payment status tracking & transaction reconciliation
- Support for multiple payment modes (IMPS/NEFT/RTGS/UPI)
- Pre-built templates for workflows and notifications
- Configurable to cater to diverse business processes

## 🚀 Why Use This Integration?

- <em>Save Time</em>: Eliminate manual bank transactions from netbanking portals
- <em>Reduce Errors</em>: Auto-sync payment data between ERPNext and Bank
- <em>Financial Control</em>: Approval workflows before initiating payouts
- <em>Secure</em>: Role based access with 2FA to authorize manual payouts

## 📦 Installation

### Frappe Cloud

Sign up for a [Frappe Cloud](https://frappecloud.com/dashboard/signup?referrer=99df7a8f) free trial, create a new site with Frappe Version-15 or above, and install ERPNext and RazorpayX-Integration from the Apps.

### Docker

Use [this guide](https://github.com/frappe/frappe_docker/blob/main/docs/custom-apps.md) to deploy RazorpayX-Integration by building your custom image.

<details>
<summary>Sample Apps JSON</summary><br>

```shell
export APPS_JSON='[
  {
    "url": "https://github.com/frappe/erpnext",
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

### Manual

Once you've [set up a Frappe site](https://frappeframework.com/docs/v14/user/en/installation/), install app by executing the following commands in your bench directory.

<details>
<summary>Using Bench CLI</summary><br>

Download the App using the Bench CLI

```sh
bench get-app https://github.com/resilient-tech/india-compliance.git
```

Install the App on your site

```sh
bench --site [site name] install-app india_compliance
```

</details>

## ⚙️ Configuration

## 📚 Documentation

## Contributing

- [Issue Guidelines](https://github.com/frappe/erpnext/wiki/Issue-Guidelines)
- [Pull Request Requirements](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)

## License

[GNU General Public License (v3)](https://github.com/resilient-tech/razorpayx-integration/blob/version-15/license.txt)
