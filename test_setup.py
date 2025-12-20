#!/usr/bin/env python3
"""
Quick test script to verify your credentials and setup.
Run this before running the full automation.
"""

import os
import sys

def check_env_vars():
    """Check if all required environment variables are set."""
    required = ['EMAIL_USER', 'EMAIL_PASS']
    missing = []

    print("🔍 Checking environment variables...\n")

    for var in required:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'PASS' in var:
                display = '*' * 8
            else:
                display = value
            print(f"✅ {var}: {display}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)

    if missing:
        print(f"\n⚠️  Missing variables: {', '.join(missing)}")
        print("\nTo set them, run:")
        for var in missing:
            print(f'export {var}="your-value-here"')
        print("\n⚠️  IMPORTANT: Use Gmail App Password, not regular password!")
        print("   Get it from: https://myaccount.google.com/apppasswords")
        return False

    print("\n✅ All environment variables are set!")
    return True


def test_gmail_connection():
    """Test Gmail IMAP connection."""
    print("\n📧 Testing Gmail connection...")

    try:
        from imap_tools import MailBox

        email_user = os.environ.get('EMAIL_USER')
        email_pass = os.environ.get('EMAIL_PASS')

        with MailBox('imap.gmail.com').login(email_user, email_pass) as mailbox:
            # Just list folders to verify connection
            folders = list(mailbox.folder.list())
            print(f"✅ Gmail connected successfully!")
            print(f"   Found {len(folders)} mail folders")
            return True

    except Exception as e:
        print(f"❌ Gmail connection failed: {e}")
        print("\n💡 Tips:")
        print("   1. Make sure you're using an App Password, not your regular password")
        print("   2. Get App Password: https://myaccount.google.com/apppasswords")
        print("   3. Enable IMAP: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP")
        return False


def test_smtp_connection():
    """Test SMTP connection for sending emails."""
    print("\n📤 Testing SMTP connection...")

    try:
        import smtplib

        email_user = os.environ.get('EMAIL_USER')
        email_pass = os.environ.get('EMAIL_PASS')

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            print(f"✅ SMTP connected successfully!")
            print(f"   Ready to send emails to {email_user}")
            return True

    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        print("\n💡 Tips:")
        print("   1. Make sure you're using an App Password, not your regular password")
        print("   2. Get App Password: https://myaccount.google.com/apppasswords")
        print("   3. The same App Password works for both IMAP and SMTP")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n📦 Checking Python dependencies...")

    required_packages = {
        'imap_tools': 'imap-tools',
        'pdfplumber': 'pdfplumber',
        'pandas': 'pandas',
        'jinja2': 'jinja2',
        'openpyxl': 'openpyxl'
    }

    missing = []

    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing packages. Install with:")
        print(f"pip install {' '.join(missing)}")
        return False

    print("\n✅ All dependencies installed!")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Financial Reconciliation Automation - Setup Checker")
    print("=" * 60)

    results = {
        'dependencies': check_dependencies(),
        'env_vars': check_env_vars(),
    }

    # Only test connections if env vars are set
    if results['env_vars']:
        results['gmail_imap'] = test_gmail_connection()
        results['gmail_smtp'] = test_smtp_connection()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = all(results.values())

    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test.upper()}: {status}")

    if all_passed:
        print("\n🎉 All tests passed! You're ready to run the automation.")
        print("\nNext step: Run the main script:")
        print("   python main.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running.")

    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
