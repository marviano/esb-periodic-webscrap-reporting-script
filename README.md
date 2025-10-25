# ESB Periodic Webscrap Reporting Script

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.0+-green.svg)](https://selenium-python.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An automated Python script that collects sales data from ESB ERP system and sends periodic reports via email. This tool helps businesses monitor their daily sales performance across multiple locations automatically.

## 🚨 Quick Fix for Common Errors

**If you get ChromeDriver errors, download the latest version:**
**🔗 https://chromedriver.chromium.org/downloads**

**Steps:** Check Chrome version → Download matching ChromeDriver → Replace `chromedriver.exe` → Restart script

## 🚀 Features

- **Automated Data Collection**: Scrapes sales data from ESB ERP system using Selenium WebDriver
- **Multi-Location Support**: Handles multiple business locations (Magelang & Bojonegoro)
- **Email Reporting**: Sends beautiful HTML email reports to stakeholders
- **Database Integration**: Stores collected data in MySQL database
- **Scheduled Execution**: Runs automatically at predefined times
- **Error Handling**: Robust retry mechanisms and error recovery
- **Security**: All sensitive data stored in environment variables

## 📋 Prerequisites

Before installing, ensure you have:

- **Python 3.7+** installed on your system
- **Google Chrome** browser installed
- **MySQL Database** access
- **Gmail Account** with App Password enabled
- **ESB ERP System** access credentials

## ⚠️ Important ChromeDriver Notice

**🚨 MOST COMMON ERROR: ChromeDriver Version Mismatch**

If you encounter errors like:
- `This version of ChromeDriver only supports Chrome version X`
- `session not created: This version of ChromeDriver only supports Chrome version X`
- `WebDriverException: unknown error: session not created`

**This means your ChromeDriver is outdated!**

**Solution:** Download the latest ChromeDriver from:
**🔗 https://chromedriver.chromium.org/downloads**

**Steps:**
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver version
3. Replace `chromedriver.exe` in project folder
4. Restart the script

## 🛠️ Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/esb-periodic-webscrap-reporting-script.git
cd esb-periodic-webscrap-reporting-script
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `selenium` - Web automation
- `mysql-connector-python` - Database connectivity
- `python-dotenv` - Environment variable management
- `requests` - HTTP requests

### Step 3: Download ChromeDriver ⚠️ CRITICAL STEP

**🚨 This is the most common source of errors!**

1. **Check your Chrome version:**
   - Open Chrome browser
   - Go to `chrome://version/`
   - Note the version number (e.g., 120.0.6099.109)

2. **Download matching ChromeDriver:**
   - Visit: **https://chromedriver.chromium.org/downloads**
   - Select the version that matches your Chrome browser
   - Download `chromedriver_win32.zip` (for Windows)

3. **Install ChromeDriver:**
   - Extract the downloaded zip file
   - Copy `chromedriver.exe` to your project root directory
   - Replace any existing `chromedriver.exe` file

4. **Verify installation:**
   - The `chromedriver.exe` should be in the same folder as your Python scripts
   - File size should be around 10-20 MB

### Step 4: Set Up Environment Variables

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your actual credentials:

   ```env
   # Email Configuration
   SENDER_EMAIL=your_email@gmail.com
   EMAIL_APP_PASSWORD=your_gmail_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587

   # Database Configuration
   DB_HOST=your_database_host
   DB_USER=your_database_username
   DB_PASSWORD=your_database_password
   DB_NAME=your_database_name

   # Account Credentials
   # Hotways Magelang Accounts
   MAGELANG_OFFLINE_USERNAME=your_magelang_offline_username
   MAGELANG_OFFLINE_PASSWORD=your_magelang_offline_password
   MAGELANG_ONLINE_USERNAME=your_magelang_online_username
   MAGELANG_ONLINE_PASSWORD=your_magelang_online_password

   # Hotways Bojonegoro Accounts
   BOJONEGORO_OFFLINE_USERNAME=your_bojonegoro_offline_username
   BOJONEGORO_OFFLINE_PASSWORD=your_bojonegoro_offline_password
   BOJONEGORO_ONLINE_USERNAME=your_bojonegoro_online_username
   BOJONEGORO_ONLINE_PASSWORD=your_bojonegoro_online_password

   # Email Recipients (comma-separated)
   ALL_LOCATIONS_RECIPIENTS=manager1@company.com,manager2@company.com
   BOJONEGORO_RECIPIENTS=bojonegoro_manager@company.com
   ```

### Step 5: Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_APP_PASSWORD`

### Step 6: Database Setup

Create the required MySQL table:

```sql
CREATE TABLE daily_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    offline_gross_sales DECIMAL(15,2) DEFAULT 0,
    online_gross_sales DECIMAL(15,2) DEFAULT 0,
    total_gross_sales DECIMAL(15,2) DEFAULT 0,
    total_pax INT DEFAULT 0,
    average_sales_per_pax DECIMAL(10,2) DEFAULT 0,
    number_of_bills INT DEFAULT 0,
    average_sales_per_bill DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_branch_date (branch, date)
);
```

## 🎯 Usage

### Option 1: Periodic Automated Reporting

Run the script for scheduled periodic reports:

```bash
python "ESB Auto Reporting.py"
```

**Features:**
- Runs continuously in background
- Executes at scheduled times: 12:00, 14:00, 16:00, 18:00, 20:00, 22:15 (GMT+7)
- Saves data to database during specific time windows
- Sends email reports to configured recipients

### Option 2: Instant Report Generation

Generate an immediate report:

```bash
python "ESB Instant Report_now.py"
```

**Features:**
- Runs once and exits
- Collects current data immediately
- Saves to database
- Sends email reports

### Option 3: Windows Batch Execution

For Windows users, you can use the provided batch file:

```bash
ESB Server Test.bat
```

## 📊 What Data is Collected

The script collects the following metrics for each location:

- **Current Sales** - Today's sales amount
- **Daily Gross Sales** - Total gross sales for the day
- **Pending Sales** - Sales awaiting completion
- **Non-Sales** - Non-sales transactions
- **Cancelled Sales** - Cancelled transactions
- **Total PAX** - Number of customers
- **Average Sales per PAX** - Revenue per customer
- **Number of Bills** - Total bills generated
- **Average Sales per Bill** - Revenue per bill

## 📧 Email Reports

The script generates beautiful HTML email reports with:

- **Professional styling** with tables and formatting
- **Location-wise breakdown** of sales data
- **Total revenue calculations**
- **Timestamp information**
- **Developer attribution**

### Report Types:
1. **All Locations Report** - Sent to management team
2. **Bojonegoro Specific Report** - Sent to Bojonegoro team

## ⚙️ Configuration

### Scheduled Times
Modify the scheduled execution times in the script:

```python
scheduled_times = [12, 14, 16, 18, 20, 22.15]  # Hours in GMT+7
```

### Retry Settings
Adjust retry mechanisms:

```python
max_overall_retries = 5      # Overall script retries
max_account_retries = 3      # Per-account retries
```

### Chrome Options
Customize Chrome behavior:

```python
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
```

## 🔧 Troubleshooting

### Common Issues

**1. 🚨 ChromeDriver Version Mismatch (MOST COMMON ERROR)**
```
Error: This version of ChromeDriver only supports Chrome version X
Error: session not created: This version of ChromeDriver only supports Chrome version X
Error: WebDriverException: unknown error: session not created
```
**Solution:** 
- **Download latest ChromeDriver:** https://chromedriver.chromium.org/downloads
- Check Chrome version: `chrome://version/`
- Download matching ChromeDriver version
- Replace `chromedriver.exe` in project folder
- **This fixes 90% of startup errors!**

**2. Gmail Authentication Error**
```
Error: Authentication failed
```
**Solution:** 
- Enable 2FA on Gmail
- Generate App Password
- Use App Password in `EMAIL_APP_PASSWORD`

**3. Database Connection Error**
```
Error: Can't connect to MySQL server
```
**Solution:**
- Verify database credentials in `.env`
- Ensure MySQL server is running
- Check network connectivity

**4. ESB Login Failed**
```
Error: Login unsuccessful
```
**Solution:**
- Verify ESB credentials in `.env`
- Check if accounts are active
- Ensure ESB server is accessible

### Debug Mode

Enable debug mode by modifying the script:

```python
test_mode = True  # Set to True for continuous testing
```

## 📁 Project Structure

```
esb-periodic-webscrap-reporting-script/
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── chromedriver.exe       # Chrome WebDriver
├── ESB Auto Reporting.py  # Main periodic script
├── ESB Instant Report_now.py # Instant report script
├── db_operations.py      # Database operations
├── ESB Server Test.bat   # Windows batch file
└── LICENSE                # MIT License
```

## 🔒 Security

- **Environment Variables**: All sensitive data stored in `.env` file
- **Git Protection**: `.env` file excluded from version control
- **App Passwords**: Gmail uses app-specific passwords
- **Database Security**: Credentials encrypted in environment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Developer

**Austin Sebastian Marviano [Axonide]**
- GitHub: [@marviano](https://github.com/marviano)
- Email: marviano.austin@gmail.com

## 🆘 Support

If you encounter any issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the error logs
3. Ensure all prerequisites are met
4. Create an issue on GitHub with detailed error information

---

**Made with ❤️ using Python, Selenium, and HTML**