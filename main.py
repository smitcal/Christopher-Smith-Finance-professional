#!/usr/bin/env python3
"""
Financial Commission Reconciliation Automation
Scans Gmail for commission statements and introducer reports,
updates master data, and emails you the results with dashboard.
"""

import os
import io
import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pdfplumber
from imap_tools import MailBox, AND
from jinja2 import Template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
MASTER_DATA_FILE = 'master_data.xlsx'
DASHBOARD_FILE = 'dashboard.html'

# Email search configuration
DAYS_BACK = 7
IMAP_SERVER = 'imap.gmail.com'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


class EmailFetcher:
    """Handles Gmail IMAP connection and attachment downloads."""

    def __init__(self, email_user, email_pass):
        self.email_user = email_user
        self.email_pass = email_pass

    def fetch_attachments(self, days_back=7):
        """
        Fetch attachments from emails in the last N days.
        Returns dict with 'pdfs' and 'excels' lists.
        """
        logger.info(f"Connecting to Gmail for {self.email_user}")
        attachments = {'pdfs': [], 'excels': []}

        try:
            with MailBox(IMAP_SERVER).login(self.email_user, self.email_pass) as mailbox:
                # Calculate date for search
                since_date = datetime.now().date() - timedelta(days=days_back)

                # Search for emails with attachments
                criteria = AND(date_gte=since_date)

                for msg in mailbox.fetch(criteria):
                    logger.info(f"Processing email: {msg.subject} from {msg.from_}")

                    for att in msg.attachments:
                        filename = att.filename.lower()

                        # Check for PDFs (Commission Statements)
                        if filename.endswith('.pdf'):
                            if 'commission' in filename or 'statement' in filename:
                                logger.info(f"Found PDF: {att.filename}")
                                attachments['pdfs'].append({
                                    'filename': att.filename,
                                    'data': att.payload
                                })

                        # Check for Excel/CSV files (Introducer Reports)
                        elif filename.endswith(('.xlsx', '.xls', '.csv')):
                            if 'introducer' in filename or 'report' in filename:
                                logger.info(f"Found Excel/CSV: {att.filename}")
                                attachments['excels'].append({
                                    'filename': att.filename,
                                    'data': att.payload
                                })

                logger.info(f"Found {len(attachments['pdfs'])} PDFs and {len(attachments['excels'])} Excel files")
                return attachments

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise


class DataProcessor:
    """Handles PDF and Excel processing and data reconciliation."""

    def __init__(self, master_file):
        self.master_file = master_file
        self.master_data = self.load_master_data()
        self.updates_made = []

    def load_master_data(self):
        """Load or create master data file."""
        if Path(self.master_file).exists():
            logger.info(f"Loading existing master data from {self.master_file}")
            df = pd.read_excel(self.master_file)
            # Ensure Case ID is string type
            if 'CaseID' in df.columns:
                df['CaseID'] = df['CaseID'].astype(str)
            return df
        else:
            logger.info("Creating new master data DataFrame")
            return pd.DataFrame()

    def process_pdf_commission_statement(self, pdf_data):
        """
        Extract commission data from PDF and update master data.
        Looks for table with: Date, BRID, Case ID, Customer, Negotiator,
        Payment Type, Reference Received, Paid
        """
        logger.info("Processing PDF commission statement")

        try:
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"Extracting tables from page {page_num + 1}")
                    tables = page.extract_tables()

                    for table in tables:
                        if not table:
                            continue

                        # Convert to DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0])

                        # Check if this looks like a commission statement
                        required_cols = ['Case ID', 'Payment Type', 'Paid']
                        if not all(col in df.columns for col in required_cols):
                            continue

                        logger.info(f"Found commission table with {len(df)} rows")

                        # Process each row
                        for idx, row in df.iterrows():
                            case_id = str(row.get('Case ID', '')).strip()
                            payment_type = str(row.get('Payment Type', '')).strip()
                            paid_str = str(row.get('Paid', '0'))

                            if not case_id or case_id == 'nan':
                                continue

                            # Clean payment amount
                            paid_amount = self._clean_currency(paid_str)

                            if paid_amount > 0:
                                self._update_payment(case_id, payment_type, paid_amount)

        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise

    def _clean_currency(self, value):
        """Remove £, commas and convert to float."""
        try:
            cleaned = re.sub(r'[£,\s]', '', str(value))
            return float(cleaned) if cleaned else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _update_payment(self, case_id, payment_type, amount):
        """Update master data with payment information."""

        # Ensure CaseID column exists
        if 'CaseID' not in self.master_data.columns:
            logger.warning("CaseID column not found in master data. Creating it.")
            self.master_data['CaseID'] = None

        # Ensure payment type column exists
        if payment_type not in self.master_data.columns:
            logger.info(f"Creating new column: {payment_type}")
            self.master_data[payment_type] = 0.0

        # Find matching row
        mask = self.master_data['CaseID'] == case_id

        if mask.any():
            # Update existing case
            current_value = self.master_data.loc[mask, payment_type].iloc[0]
            current_value = 0.0 if pd.isna(current_value) else float(current_value)
            new_value = current_value + amount

            self.master_data.loc[mask, payment_type] = new_value
            logger.info(f"Updated Case {case_id}: {payment_type} = £{new_value:.2f}")
            self.updates_made.append(case_id)
        else:
            # Create new row for this case
            logger.info(f"Creating new case entry: {case_id}")
            new_row = {'CaseID': case_id, payment_type: amount}
            self.master_data = pd.concat([self.master_data, pd.DataFrame([new_row])], ignore_index=True)
            self.updates_made.append(case_id)

    def process_excel_introducer_report(self, excel_data, filename):
        """
        Process introducer report (new leads).
        Expected columns: Priority, Created, CaseID, Report Name,
        Full Names, Status, Advisor, etc.
        """
        logger.info(f"Processing introducer report: {filename}")

        try:
            # Read Excel or CSV
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(excel_data))
            else:
                df = pd.read_excel(io.BytesIO(excel_data))

            # Ensure CaseID is string
            if 'CaseID' in df.columns:
                df['CaseID'] = df['CaseID'].astype(str)
            else:
                logger.error("No CaseID column found in introducer report")
                return

            logger.info(f"Found {len(df)} cases in introducer report")

            # Initialize master data columns if empty
            if self.master_data.empty:
                self.master_data = pd.DataFrame(columns=df.columns)

            # Process each case
            for idx, row in df.iterrows():
                case_id = str(row['CaseID']).strip()

                if not case_id or case_id == 'nan':
                    continue

                # Check if case exists
                mask = self.master_data['CaseID'] == case_id

                if mask.any():
                    # Update status only
                    if 'Status' in row and 'Status' in self.master_data.columns:
                        old_status = self.master_data.loc[mask, 'Status'].iloc[0]
                        new_status = row['Status']
                        if old_status != new_status:
                            self.master_data.loc[mask, 'Status'] = new_status
                            logger.info(f"Updated Case {case_id}: Status {old_status} → {new_status}")
                            self.updates_made.append(case_id)
                else:
                    # Add new case
                    logger.info(f"Adding new case: {case_id}")
                    self.master_data = pd.concat([self.master_data, pd.DataFrame([row])], ignore_index=True)
                    self.updates_made.append(case_id)

        except Exception as e:
            logger.error(f"Error processing Excel file: {e}")
            raise

    def save_master_data(self):
        """Save updated master data to Excel."""
        logger.info(f"Saving master data to {self.master_file}")
        self.master_data.to_excel(self.master_file, index=False)
        logger.info(f"Saved {len(self.master_data)} records")


class DashboardGenerator:
    """Generates HTML dashboard from master data."""

    def __init__(self, data, updated_case_ids):
        self.data = data
        self.updated_case_ids = updated_case_ids

    def generate_html(self):
        """Generate Bootstrap 5 HTML dashboard."""
        logger.info("Generating HTML dashboard")

        # Calculate summary statistics
        payment_columns = [col for col in self.data.columns
                          if 'Fee' in col or 'Payment' in col or 'Proc' in col]

        total_commission = 0.0
        for col in payment_columns:
            total_commission += self.data[col].sum() if col in self.data.columns else 0.0

        completed_cases = 0
        if 'Status' in self.data.columns:
            completed_cases = self.data[self.data['Status'].str.contains('Complete', case=False, na=False)].shape[0]

        # Prepare data for table
        table_html = self._generate_table()

        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <title>Commission Dashboard - Private</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            padding: 20px;
        }
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .stat-box {
            text-align: center;
            padding: 15px;
        }
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        .table-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .search-box {
            margin-bottom: 20px;
        }
        .highlight-row {
            background-color: #d4edda !important;
        }
        .table-responsive {
            max-height: 600px;
            overflow-y: auto;
        }
        table thead th {
            position: sticky;
            top: 0;
            background-color: #495057;
            color: white;
            z-index: 10;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #6c757d;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-12">
                <h1 class="text-center mb-4">📊 Commission Dashboard</h1>
                <p class="text-center text-muted">Last Updated: {{ last_updated }}</p>
            </div>
        </div>

        <!-- Summary Cards -->
        <div class="summary-card">
            <div class="row">
                <div class="col-md-6">
                    <div class="stat-box">
                        <div class="stat-value">£{{ total_commission }}</div>
                        <div class="stat-label">Total Commission</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="stat-box">
                        <div class="stat-value">{{ completed_cases }}</div>
                        <div class="stat-label">Cases Completed</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="table-container">
            <div class="search-box">
                <input type="text"
                       id="searchInput"
                       class="form-control"
                       placeholder="🔍 Search by Case ID, Customer Name, Status...">
            </div>

            <div class="table-responsive">
                {{ table_html|safe }}
            </div>
        </div>

        <div class="footer">
            <p>Private Dashboard - Confidential Information</p>
            <p>Generated by Automated Commission Reconciliation System</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Search functionality
        document.getElementById('searchInput').addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#dataTable tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchValue) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
        """

        template = Template(html_template)

        html_content = template.render(
            last_updated=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_commission=f"{total_commission:,.2f}",
            completed_cases=completed_cases,
            table_html=table_html
        )

        return html_content

    def _generate_table(self):
        """Generate HTML table from data."""
        if self.data.empty:
            return '<p class="text-center text-muted">No data available</p>'

        # Add row highlighting class
        def row_class(row):
            case_id = str(row.get('CaseID', ''))
            status = str(row.get('Status', ''))

            if case_id in self.updated_case_ids or 'complete' in status.lower():
                return 'class="highlight-row"'
            return ''

        table_html = '<table class="table table-striped table-hover" id="dataTable">\n<thead>\n<tr>\n'

        # Headers
        for col in self.data.columns:
            table_html += f'<th>{col}</th>\n'

        table_html += '</tr>\n</thead>\n<tbody>\n'

        # Rows
        for idx, row in self.data.iterrows():
            row_classes = row_class(row)
            table_html += f'<tr {row_classes}>\n'

            for col in self.data.columns:
                value = row[col]

                # Format currency columns
                if any(keyword in col for keyword in ['Fee', 'Payment', 'Proc', 'Paid']):
                    if pd.notna(value) and value != 0:
                        value = f"£{float(value):,.2f}"
                    else:
                        value = '-'
                elif pd.isna(value):
                    value = ''

                table_html += f'<td>{value}</td>\n'

            table_html += '</tr>\n'

        table_html += '</tbody>\n</table>'

        return table_html


class EmailSender:
    """Handles sending email reports with attachments."""

    def __init__(self, email_user, email_pass):
        self.email_user = email_user
        self.email_pass = email_pass
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT

    def send_report(self, emails_processed, total_commission, master_file, dashboard_file):
        """
        Send email with commission reconciliation report.

        Args:
            emails_processed: Number of emails processed
            total_commission: Total commission amount found
            master_file: Path to master data Excel file
            dashboard_file: Path to HTML dashboard
        """
        logger.info(f"Preparing email report to {self.email_user}")

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user
            msg['Subject'] = f"Commission Reconciliation Report - {datetime.now().strftime('%Y-%m-%d')}"

            # Email body
            body = f"""
Commission Reconciliation Automation Report
{"=" * 50}

Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
- Emails Processed: {emails_processed}
- Total Commission Found This Run: £{total_commission:,.2f}

Files attached:
1. master_data.xlsx - Your complete commission database
2. dashboard.html - Interactive dashboard (open in browser)

Next Steps:
- Open dashboard.html in your browser to view the interactive report
- Review master_data.xlsx for all commission details
- Check for any cases marked with green highlighting (recent updates)

{"=" * 50}
This is an automated report from your Commission Reconciliation System.
            """

            msg.attach(MIMEText(body, 'plain'))

            # Attach master data Excel file
            if Path(master_file).exists():
                logger.info(f"Attaching {master_file}")
                with open(master_file, 'rb') as f:
                    part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(master_file)}')
                    msg.attach(part)

            # Attach dashboard HTML
            if Path(dashboard_file).exists():
                logger.info(f"Attaching {dashboard_file}")
                with open(dashboard_file, 'rb') as f:
                    part = MIMEBase('text', 'html')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(dashboard_file)}')
                    msg.attach(part)

            # Send email
            logger.info(f"Connecting to {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                logger.info("Starting TLS encryption")

                server.login(self.email_user, self.email_pass)
                logger.info(f"Logged in as {self.email_user}")

                server.send_message(msg)
                logger.info("✅ Email sent successfully!")

        except Exception as e:
            logger.error(f"Email sending error: {e}")
            raise


def main():
    """Main execution flow."""
    logger.info("=== Starting Financial Reconciliation Automation ===")

    # Validate environment variables
    required_vars = ['EMAIL_USER', 'EMAIL_PASS']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise ValueError("Missing required environment variables")

    try:
        # Step 1: Fetch emails and attachments
        fetcher = EmailFetcher(EMAIL_USER, EMAIL_PASS)
        attachments = fetcher.fetch_attachments(days_back=DAYS_BACK)

        total_emails = len(attachments['pdfs']) + len(attachments['excels'])

        # Step 2: Process data
        processor = DataProcessor(MASTER_DATA_FILE)

        # Process PDFs (Commission Statements)
        for pdf in attachments['pdfs']:
            logger.info(f"Processing PDF: {pdf['filename']}")
            processor.process_pdf_commission_statement(pdf['data'])

        # Process Excel files (Introducer Reports)
        for excel in attachments['excels']:
            logger.info(f"Processing Excel: {excel['filename']}")
            processor.process_excel_introducer_report(excel['data'], excel['filename'])

        # Save updated master data
        processor.save_master_data()

        # Step 3: Generate HTML dashboard
        generator = DashboardGenerator(processor.master_data, processor.updates_made)
        html_content = generator.generate_html()

        # Save HTML locally
        with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Dashboard saved to {DASHBOARD_FILE}")

        # Step 4: Calculate total commission
        payment_columns = [col for col in processor.master_data.columns
                          if 'Fee' in col or 'Payment' in col or 'Proc' in col]

        total_commission = 0.0
        for col in payment_columns:
            total_commission += processor.master_data[col].sum() if col in processor.master_data.columns else 0.0

        # Step 5: Email the results
        sender = EmailSender(EMAIL_USER, EMAIL_PASS)
        sender.send_report(
            emails_processed=total_emails,
            total_commission=total_commission,
            master_file=MASTER_DATA_FILE,
            dashboard_file=DASHBOARD_FILE
        )

        logger.info("=== Automation Complete ===")
        logger.info(f"Emails processed: {total_emails}")
        logger.info(f"Total commission: £{total_commission:,.2f}")
        logger.info(f"Total updates made: {len(set(processor.updates_made))}")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
