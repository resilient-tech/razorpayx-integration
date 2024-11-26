# RazorpayX Integration

Automat Payments By RazorPayX API For Frappe Apps

## Code Formatting & Linting

This repository uses [pre-commit](https://pre-commit.com) to ensure that basic code style and correctness requirements are met before merging any PRs. While the suite of linting/formatting tools might keep evolving you just need to install `pre-commit` to get started. It will install and configure the required tools.

### Installing pre-commit

```bash
cd apps/razorpayx_integration
pip install pre-commit
```

### Adding pre-commit hook to git

```bash
pre-commit install
```

This will configure a git pre-commit hook which will ensure that your changes pass bare-minimum style/correctness requirements for accepting the changes.

#### Usage

Pre-commit runs automatically while trying to commit changes:

![Pre-Commit Run Image](https://github.com/user-attachments/assets/0ba0aa50-f510-4d6e-ab65-f14d069bfee0)

If there are  changes done by `pre-commit`, you need to add them to the staging area and retry committing.

You can skip running pre-commit by passing the `-n` flag like so:

```bash
git commit -n
```

Current checks:

* Whitespace trimming (style)
* ruff - linting, formatting, import sorting for python
* prettier - formatting JS files
* eslint - linter for JS files

## License

MIT
