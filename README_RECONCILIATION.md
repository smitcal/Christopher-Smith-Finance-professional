# Financial Commission Reconciliation Automation

Automated system for mortgage brokers to reconcile commission reports and publish a private dashboard.

## 📋 Overview

This Python automation suite:
- 📧 Scans Gmail for commission statements (PDFs) and introducer reports (Excel/CSV)
- 💰 Updates a master Excel file with new leads and payment data
- 📊 Generates a mobile-friendly HTML dashboard with Bootstrap 5
- 🚀 Uploads the dashboard to your website via FTP
- ⏰ Runs automatically every 6 hours via GitHub Actions

## 🏗️ Architecture

```
┌─────────────┐
│   Gmail     │ → Fetches PDFs & Excel files
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Data Processor │ → Reconciles commission & leads
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Master Data     │ → master_data.xlsx (persistent)
│ Excel File      │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ HTML Generator  │ → Creates responsive dashboard
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  FTP Uploader   │ → Publishes to website
└─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Gmail account with IMAP enabled
- FTP access to your website
- GitHub account (for automation)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-directory>

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Gmail credentials
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASS="your-app-password"  # See Gmail App Password setup below

# FTP credentials
export FTP_HOST="ftp.yourwebsite.com"
export FTP_USER="your-ftp-username"
export FTP_PASS="your-ftp-password"
export FTP_DIRECTORY="/public_html/private_dashboard/"  # Optional, has default
```

### 4. Gmail App Password Setup

1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Go to "App passwords"
4. Generate a new app password for "Mail"
5. Use this 16-character password as `EMAIL_PASS`

### 5. Run Locally

```bash
python main.py
```

This will:
- Scan your Gmail for the last 7 days
- Process any commission statements and introducer reports
- Update `master_data.xlsx`
- Generate `commission_dashboard_private.html`
- Upload the dashboard to your website

## ⚙️ GitHub Actions Setup

### 1. Configure Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `EMAIL_USER`: Your Gmail address
- `EMAIL_PASS`: Your Gmail app password
- `FTP_HOST`: FTP server address
- `FTP_USER`: FTP username
- `FTP_PASS`: FTP password
- `FTP_DIRECTORY`: FTP directory path (optional)

### 2. Workflow Schedule

The workflow runs:
- ⏰ **Automatically**: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)
- 🖱️ **Manually**: Via "Actions" tab → "Run workflow"

### 3. Monitor Runs

- Go to Actions tab in your GitHub repository
- View logs for each run
- Download `master_data.xlsx` artifacts from completed runs

## 📁 File Structure

```
.
├── main.py                           # Main automation script
├── requirements.txt                  # Python dependencies
├── master_data.xlsx                  # Your master database (auto-created)
├── commission_dashboard_private.html # Generated dashboard
├── .github/
│   └── workflows/
│       └── main.yml                  # GitHub Actions workflow
└── README_RECONCILIATION.md          # This file
```

## 📊 Data Processing Logic

### PDF Commission Statements

**Expected Table Structure:**
```
| Date | BRID | Case ID | Customer | Negotiator | Payment Type | Reference Received | Paid |
```

**Processing:**
1. Extracts tables from all pages
2. Cleans currency values (removes £, commas)
3. Finds matching `Case ID` in master data
4. Creates/updates column named after `Payment Type`
5. Adds payment amount to existing value

**Example:**
- PDF shows: `Case ID: 12345, Payment Type: "Proc Fee", Paid: £500.00`
- Creates column "Proc Fee" if doesn't exist
- Updates Case 12345's "Proc Fee" value by adding £500

### Excel Introducer Reports

**Expected Columns:**
```
Priority, Created, CaseID, Report Name, Full Names, Status, Advisor, ...
```

**Processing:**
1. Reads Excel/CSV file
2. For each case:
   - **New Case**: Adds entire row to master data
   - **Existing Case**: Updates `Status` column only
3. Tracks all updates for dashboard highlighting

## 🎨 Dashboard Features

### Summary Cards
- 💷 **Total Commission**: Sum of all payment columns
- ✅ **Cases Completed**: Count of cases with "Complete" status

### Interactive Table
- 🔍 **Live Search**: Filter by Case ID, Customer, Status, etc.
- 📱 **Mobile Responsive**: Bootstrap 5 responsive design
- 🎨 **Conditional Formatting**: Green highlighting for:
  - Completed cases
  - Cases updated in this run

### Security
- `noindex, nofollow` meta tags (not indexed by Google)
- Obscure filename: `commission_dashboard_private.html`
- Served from private directory

## 🔧 Customization

### Change Email Search Window

Edit `main.py`:
```python
DAYS_BACK = 7  # Change to desired number of days
```

### Modify Dashboard Styling

Edit the `<style>` section in `DashboardGenerator.generate_html()`:
```python
# Change colors, fonts, layout, etc.
```

### Add Custom Columns

The system automatically creates columns based on:
- Payment types found in PDFs
- Columns in introducer reports

No code changes needed!

## 🐛 Troubleshooting

### "No attachments found"

**Causes:**
- Email search criteria too restrictive
- Attachments don't match filename patterns

**Solutions:**
1. Check email subjects contain keywords
2. Adjust filename matching in `EmailFetcher.fetch_attachments()`:
   ```python
   if 'commission' in filename or 'statement' in filename:
   ```

### "Login failed" (Gmail)

**Causes:**
- Wrong app password
- IMAP not enabled
- 2FA not set up

**Solutions:**
1. Verify app password is correct (16 characters, no spaces)
2. Enable IMAP: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP
3. Set up 2FA first, then generate app password

### "FTP upload failed"

**Causes:**
- Wrong credentials
- Directory doesn't exist
- Permissions issue

**Solutions:**
1. Test FTP credentials with FileZilla or similar
2. Script auto-creates directories, but check permissions
3. Verify `FTP_DIRECTORY` path is correct

### "PDF table not found"

**Causes:**
- PDF format doesn't match expected structure
- Table extraction failed

**Solutions:**
1. Check PDF manually - does it have the expected columns?
2. Add logging to see extracted tables:
   ```python
   logger.info(f"Columns found: {df.columns.tolist()}")
   ```
3. Adjust column matching logic if needed

## 📈 Best Practices

### 1. Backup Master Data

The workflow saves artifacts, but also:
```bash
# Backup before running
cp master_data.xlsx master_data_backup_$(date +%Y%m%d).xlsx
```

### 2. Test Locally First

```bash
# Run with limited scope
python main.py  # Processes last 7 days
```

Review `master_data.xlsx` before deploying to GitHub Actions.

### 3. Monitor Logs

Check GitHub Actions logs regularly:
- Verify data is being processed
- Check for errors
- Monitor update counts

### 4. Validate Data

Periodically spot-check:
- Dashboard vs commission statements
- Master data vs source reports
- Payment totals

## 🔐 Security Considerations

### Sensitive Data

- ✅ **Never commit** `master_data.xlsx` to public repos
- ✅ **Never commit** `.env` files
- ✅ **Use GitHub Secrets** for all credentials
- ✅ **Dashboard** is private (noindex + obscure URL)

### Add to `.gitignore`:

```
master_data.xlsx
*.env
commission_dashboard_private.html
```

## 📞 Support

### Common Issues

1. **No updates detected**: Check email date range and attachment filenames
2. **Wrong totals**: Verify PDF table structure matches expected format
3. **FTP issues**: Test credentials with FTP client first
4. **Dashboard not updating**: Check FTP upload logs

### Logs

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)  # In main.py
```

## 🎯 Future Enhancements

Potential improvements:
- [ ] Add email notifications on errors
- [ ] Support multiple email accounts
- [ ] Add data validation rules
- [ ] Create weekly summary reports
- [ ] Add authentication to dashboard
- [ ] Support more PDF formats
- [ ] Add data export (CSV, JSON)

## 📄 License

Private use for mortgage brokerage operations.

## 🙏 Credits

Built with:
- [imap-tools](https://github.com/ikvk/imap_tools) - Email processing
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF extraction
- [pandas](https://pandas.pydata.org/) - Data processing
- [Bootstrap 5](https://getbootstrap.com/) - Dashboard UI
- [Jinja2](https://jinja.palletsprojects.com/) - HTML templating

---

**Last Updated**: 2025-12-20
**Version**: 1.0.0
