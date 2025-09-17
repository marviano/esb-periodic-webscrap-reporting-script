# ESB Periodic Webscrap Reporting Script

This script automatically collects sales data from ESB ERP system and sends periodic reports via email.

## Setup Instructions

1. **Install Dependencies**
   `ash
   pip install -r requirements.txt
   `

2. **Environment Configuration**
   - Copy .env.example to .env
   - Fill in your actual credentials in the .env file:
     - Email configuration (Gmail app password)
     - Database connection details
     - Account credentials for ESB ERP system
     - Email recipients

3. **Gmail App Password Setup**
   - Enable 2-factor authentication on your Gmail account
   - Generate an app password for this application
   - Use the app password in EMAIL_APP_PASSWORD field

4. **Run the Script**
   - For periodic reporting: python "ESB Auto Reporting.py"
   - For instant report: python "ESB Instant Report_now.py"

## Security Notes

- Never commit the .env file to version control
- The .env file contains sensitive information and is already added to .gitignore
- Use .env.example as a template for other users

## Files

- ESB Auto Reporting.py - Main periodic reporting script
- ESB Instant Report_now.py - Instant report generation
- db_operations.py - Database operations
- .env - Environment variables (create from .env.example)
- .env.example - Template for environment variables
- equirements.txt - Python dependencies
