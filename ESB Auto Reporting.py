import os
import time
import requests
import traceback
import smtplib
# from zoneinfo import ZoneInfo  # Add this line
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime, timezone, timedelta

def wait_for_non_zero_text(driver, element_id, timeout=30):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.ID, element_id).text.strip() not in ['0', '']
        )
        return True
    except TimeoutException:
        return False

def logout(driver, username):
    dropdown_toggle = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "toggle-account"))
    )
    dropdown_toggle.click()
    print("Clicked account dropdown")

    logout_link = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='/site/logout'][@data-method='post']"))
    )
    logout_link.click()
    print(f"Clicked logout for {username}")

    WebDriverWait(driver, 10).until(
        EC.url_contains('https://erp.esb.co.id/site/login')
    )
    print(f"Successfully logged out {username}")

def handle_connection_error(driver, username):
    print(f"Handling potential connection error for {username}")
    try:
        driver.refresh()
        print(f"Page refreshed for {username}")
        time.sleep(5)
        logout(driver, username)
    except Exception as e:
        print(f"Error during connection error handling for {username}: {e}")
        print("Unable to recover. Moving to next account or iteration.")

def login_and_extract_data(driver, username, password, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} for {username}")
            driver.get('https://erp.esb.co.id/site/login')
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginform-username')))
            driver.find_element(By.ID, 'loginform-username').send_keys(username)
            driver.find_element(By.ID, 'loginform-password').send_keys(password)
            driver.find_element(By.ID, 'btnLogin').click()
            
            try:
                confirm_button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'swal2-confirm')]"))
                )
                confirm_button.click()
                print("Clicked confirmation button on the dialog.")
            except TimeoutException:
                print("No confirmation dialog appeared or couldn't click confirm.")

            WebDriverWait(driver, 10).until(
                EC.url_changes('https://erp.esb.co.id/site/login')
            )
            print(f"Login successful for {username}")

            driver.get('https://erp.esb.co.id/sales-dashboard')
            print(f"Navigated to dashboard for {username}")
            
            if not wait_for_non_zero_text(driver, 'todayHighlightCurrentSales'):
                print(f"No sales data available for {username}")
                return "NO_DATA"
            
            data = {}
            elements = [
                'todayHighlightCurrentSales', 'todayHighlightcurrentDailyGrossSales',
                'todayHighlightPendingSales', 'todayHighlightRemoveMenuBeforeSave',
                'todayHighlightNonSales', 'todayHighlightCancelledSales',
                'todayHighlightPaxTotal', 'todayHighlightAverageNetSalesPerPax',
                'todayHighlightNumberOfBill', 'todayHighlightAverageNetSalesPerBill'
            ]
            
            for element_id in elements:
                try:
                    data[element_id] = driver.find_element(By.ID, element_id).text
                except NoSuchElementException:
                    print(f"Element {element_id} not found for {username}")
                    data[element_id] = "N/A"
            
            print(f"\nData extracted for {username}:")
            for key, value in data.items():
                print(f"{key}: {value}")
            
            try:
                logout(driver, username)
            except Exception as e:
                print(f"Error during logout for {username}: {e}")
                handle_connection_error(driver, username)
            
            return data

        except Exception as e:
            print(f"Error occurred for {username}: {e}")
            print(traceback.format_exc())
            handle_connection_error(driver, username)
        
        time.sleep(5)
    
    print(f"Failed to retrieve data for {username} after {max_retries} attempts")
    return "ERROR"

def create_beautiful_email(data, report_type, include_footer=True):
    current_time = datetime.now(timezone.utc) + timedelta(hours=7)
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S GMT+7")

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1 {{ color: #0066cc; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; color: #0066cc; }}
            .total {{ font-weight: bold; background-color: #e6f2ff; }}
            .grand-total {{ 
                font-size: 1.2em; 
                font-weight: bold; 
                color: #009900; 
                background-color: #e6f2ff; 
                padding: 15px; 
                border: 2px solid #0066cc; 
                border-radius: 5px; 
                margin-top: 20px; 
                text-align: center;
            }}
            .footer {{ font-size: 0.8em; color: #666; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
    """
    
    if report_type == "All":
        html += f"<h1>Daily Sales Report - All Locations</h1>"
        locations = ["Hotways Ponorogo", "Hotways Magelang", "Hotways Bojonegoro"]
    elif report_type == "Ponorogo and Bojonegoro":
        html += f"<h1>Daily Sales Report - Ponorogo and Bojonegoro</h1>"
        locations = ["Hotways Ponorogo", "Hotways Bojonegoro"]
    else:
        html += f"<h1>Daily Sales Report - {report_type}</h1>"
        locations = [report_type]

    html += f"<p>Generated on: {formatted_time}</p>"

    grand_total = 0
    for loc in locations:
        offline_data = data.get(f"{loc} Offline", {})
        online_data = data.get(f"{loc} Online", {})
        
        offline_sales = float(offline_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
        online_sales = float(online_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
        total_sales = offline_sales + online_sales
        grand_total += total_sales

        html += f"""
        <h2>{loc}</h2>
        <table>
            <tr>
                <th>Category</th>
                <th>Gross Sales</th>
            </tr>
            <tr>
                <td>Offline Gross Sales</td>
                <td>Rp {offline_sales:,.0f}</td>
            </tr>
            <tr>
                <td>Online Gross Sales</td>
                <td>Rp {online_sales:,.0f}</td>
            </tr>
            <tr class="total">
                <td>Total Gross Sales</td>
                <td>Rp {total_sales:,.0f}</td>
            </tr>
        </table>
        """

    # Add grand total with simplified text and green color
    html += f"""
    <div class="grand-total">
        Total Omset = Rp {grand_total:,.0f}
    </div>
    """

    if include_footer:
        html += """
            <div class="footer">
                <p>Developed by: Austin Sebastian Marviano [Axonide]</p>
                <p><a href="https://github.com/marviano">github.com/marviano</a></p>
                <p>Made with: Python, Selenium, HTML</p>
            </div>
        """

    html += """
    </body>
    </html>
    """
    return html

def send_email(subject, body, to_email):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "marviano.austin@gmail.com"
    app_password = "ktqbdhbktmcdkvuf"

    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["Subject"] = subject
    
    if isinstance(to_email, str):
        to_emails = [to_email]
    else:
        to_emails = to_email
        
    message["To"] = ", ".join(to_emails)

    message.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(message)
        print(f"Email sent successfully to {', '.join(to_emails)}")
    except Exception as e:
        print(f"Error sending email: {e}")

def main():
    accounts = [
        {"name": "Hotways Magelang Offline", "username": "hcc38sales", "password": "-@}5M2=C1`Ud?"},
        {"name": "Hotways Magelang Online", "username": "hc38psales", "password": "-@}5M2=C1`Ud?"},
        {"name": "Hotways Ponorogo Offline", "username": "hcc39sales", "password": "cz2F`a&Ki2;7#"},
        {"name": "Hotways Ponorogo Online", "username": "hc39psales", "password": "cz2F`a&Ki2;7#"},
        {"name": "Hotways Bojonegoro Offline", "username": "hcc41sales", "password": "09272024Bojonegoro!"},
        {"name": "Hotways Bojonegoro Online", "username": "hc41psales", "password": "09272024Bojonegoro!"}
    ]

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop', 'chromedriver.exe'))
    
    max_overall_retries = 5
    max_account_retries = 3

    for overall_attempt in range(max_overall_retries):
        try:
            all_data = {}
            driver = webdriver.Chrome(service=service, options=chrome_options)
            chrome_version = driver.capabilities['browserVersion']
            chromedriver_version = driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0]
            print(f"Chrome version: {chrome_version}")
            print(f"ChromeDriver version: {chromedriver_version}")

            for account in accounts:
                account_success = False
                for account_attempt in range(max_account_retries):
                    print(f"\nProcessing account: {account['name']} (Attempt {account_attempt + 1})")
                    result = login_and_extract_data(driver, account["username"], account["password"])
                    if result == "NO_DATA":
                        print(f"No sales data available for {account['name']}. Moving to next account.")
                        account_success = True
                        break
                    elif result == "ERROR":
                        print(f"Error occurred for {account['name']}. Retrying...")
                    else:
                        all_data[account["name"]] = result
                        print(f"Data successfully retrieved for {account['name']}")
                        account_success = True
                        break
                    
                    if account_attempt < max_account_retries - 1:
                        print(f"Retrying {account['name']} in 30 seconds...")
                        time.sleep(30)
                
                if not account_success:
                    print(f"Failed to retrieve data for {account['name']} after {max_account_retries} attempts")
                
                time.sleep(5)

            # Process and send emails only if we have data
            if all_data:
                summary = "Summary:\n"
                for location in ["Hotways Ponorogo", "Hotways Magelang", "Hotways Bojonegoro"]:
                    offline_data = all_data.get(f"{location} Offline", {})
                    online_data = all_data.get(f"{location} Online", {})
                    
                    offline_sales = float(offline_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
                    online_sales = float(online_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
                    
                    total_sales = offline_sales + online_sales
                    
                    summary += f"{location}\n"
                    summary += f"Offline Gross Sales: {offline_sales:,.0f}\n"
                    summary += f"Online Gross Sales: {online_sales:,.0f}\n"
                    summary += f"Total Gross Sales: {total_sales:,.0f}\n\n"

                print(summary)
                
            # Send data for all locations to the first group of recipients
            all_locations_email = create_beautiful_email(all_data, "All")
            all_locations_recipients = ["alvusebastian@gmail.com", "bart2000e@gmail.com", "headofficemilman@gmail.com", "reni.dnh2904@gmail.com", "rudihoo1302@gmail.com", "jenny_sulistiowati68@yahoo.com", "sony_hendarto@hotmail.com"]
            # all_locations_recipients = ["alvusebastian@gmail.com"]
            send_email("Hotways Periodic Report - All Locations", all_locations_email, all_locations_recipients)

            # Send Ponorogo and Bojonegoro data to the second group of recipients
            ponorogo_bojonegoro_data = {k: v for k, v in all_data.items() if "Ponorogo" in k or "Bojonegoro" in k}
            ponorogo_bojonegoro_email = create_beautiful_email(ponorogo_bojonegoro_data, "Ponorogo and Bojonegoro")
            ponorogo_bojonegoro_recipients = ["alvusebastian@gmail.com", "yudi_soetrisno70@yahoo.com"]
            # ponorogo_bojonegoro_recipients = ["alvusebastian@gmail.com"]
            send_email("Hotways Periodic Report - Ponorogo and Bojonegoro", ponorogo_bojonegoro_email, ponorogo_bojonegoro_recipients)

            # If we've made it here, everything was successful, so we can break the retry loop
            break

        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            if "This version of ChromeDriver only supports Chrome version" in str(e):
                print("There's a version mismatch between ChromeDriver and Chrome.")
                print("Please download the correct ChromeDriver version from:")
                print("https://googlechromelabs.github.io/chrome-for-testing/")
            elif "session not created" in str(e):
                print("Session could not be created. This might be due to a version mismatch or a corrupted ChromeDriver.")
                print("Try downloading a matching ChromeDriver version from:")
                print("https://googlechromelabs.github.io/chrome-for-testing/")
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
        finally:
            driver.quit()

        if overall_attempt < max_overall_retries - 1:
            print(f"Overall attempt {overall_attempt + 1} failed. Restarting from the beginning in 60 seconds...")
            time.sleep(60)
        else:
            print("All overall attempts failed. Please check your internet connection and try again later.")

if __name__ == "__main__":
    WIB = timezone(timedelta(hours=7))  # Western Indonesia Time (GMT+7)
    scheduled_times = [12, 14, 16, 18, 20, 22.15]
    time_buffer = timedelta(minutes=5)  # Allow a 5-minute buffer after each scheduled time
    
    while True:
        current_time = datetime.now(WIB)
        print(f"Current time (WIB/GMT+7): {current_time}")
        
        # Check if we're within the buffer period of any scheduled time
        for hour in scheduled_times:
            scheduled_time = current_time.replace(hour=int(hour), minute=int((hour % 1) * 60), second=0, microsecond=0)
            if scheduled_time <= current_time <= scheduled_time + time_buffer:
                print(f"Running report for scheduled time: {scheduled_time}")
                main()
                # Sleep for the buffer period to avoid multiple executions
                time.sleep(time_buffer.total_seconds())
                break
        else:
            # Find the next scheduled time
            next_run = None
            for hour in scheduled_times:
                scheduled_time = current_time.replace(hour=int(hour), minute=int((hour % 1) * 60), second=0, microsecond=0)
                if current_time < scheduled_time:
                    next_run = scheduled_time
                    break
            
            # If we've passed the last scheduled time for today, set next_run to the first time tomorrow
            if next_run is None:
                next_run = current_time.replace(hour=int(scheduled_times[0]), minute=int((scheduled_times[0] % 1) * 60), second=0, microsecond=0) + timedelta(days=1)
            
            # Calculate sleep time
            sleep_seconds = (next_run - current_time).total_seconds()
            
            print(f"Next run scheduled for: {next_run}")
            print(f"Sleeping for {sleep_seconds:.0f} seconds")
            
            # Sleep until the next scheduled time
            time.sleep(min(sleep_seconds, 60))  # Check at least every minute