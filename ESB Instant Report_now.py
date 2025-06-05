import os
import time
import requests
import traceback
import smtplib
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
from db_operations import save_to_database
WIB = timezone(timedelta(hours=7))  # Western Indonesia Time (GMT+7)

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
        locations = ["Hotways Magelang", "Hotways Bojonegoro"]
    elif report_type == "Bojonegoro":
        html += f"<h1>Daily Sales Report - Bojonegoro</h1>"
        locations = ["Hotways Bojonegoro"]
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

def is_within_save_window(current_time, scheduled_times, grace_period_minutes=15):
    for scheduled_hour in scheduled_times:
        scheduled_time = current_time.replace(hour=int(scheduled_hour), minute=int((scheduled_hour % 1) * 60), second=0, microsecond=0)
        if scheduled_time <= current_time <= scheduled_time + timedelta(minutes=grace_period_minutes):
            return True
    return False

def main():
    accounts = [
        {"name": "Hotways Magelang Offline", "username": "hcc38sales", "password": "-@}5M2=C1`Ud?"},
        {"name": "Hotways Magelang Online", "username": "hc38psales", "password": "-@}5M2=C1`Ud?"},
        {"name": "Hotways Bojonegoro Offline", "username": "hcc41sales", "password": "09272024Bojonegoro!"},
        {"name": "Hotways Bojonegoro Online", "username": "hc41psales", "password": "09272024Bojonegoro!"}
    ]

    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    chromedriver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
    service = Service(chromedriver_path)
    
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
                        time.sleep(5)  # Short delay between retries
                
                if not account_success:
                    print(f"Failed to retrieve data for {account['name']} after {max_account_retries} attempts")
                
                time.sleep(2)  # Short delay between accounts

            if all_data:
                # Print summary
                summary = "Summary:\n"
                for location in ["Hotways Magelang", "Hotways Bojonegoro"]:
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
            
                # Save to database
                print("Saving data to database...")
                save_to_database(all_data)
                print("Data saved successfully")
                
                # Send emails
                all_locations_email = create_beautiful_email(all_data, "All")
                all_locations_recipients = ["alvusebastian@gmail.com", "bart2000e@gmail.com", "headofficemilman@gmail.com", "reni.dnh2904@gmail.com", "rudihoo1302@gmail.com", "jenny_sulistiowati68@yahoo.com", "sony_hendarto@hotmail.com"]
                # all_locations_recipients = ["alvusebastian@gmail.com"]
                send_email("Hotways Periodic Report - All Locations", all_locations_email, all_locations_recipients)

                bojonegoro_data = {k: v for k, v in all_data.items() if "Bojonegoro" in k}
                bojonegoro_email = create_beautiful_email(bojonegoro_data, "Bojonegoro")
                bojonegoro_recipients = ["alvusebastian@gmail.com", "yudi_soetrisno70@yahoo.com"]
                # bojonegoro_recipients = ["alvusebastian@gmail.com"]
                send_email("Hotways Periodic Report - Bojonegoro", bojonegoro_email, bojonegoro_recipients)

            # If we've made it here, everything was successful
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
            print(f"Overall attempt {overall_attempt + 1} failed. Retrying in 5 seconds...")
            time.sleep(5)
        else:
            print("All overall attempts failed. Please check your internet connection and try again later.")

if __name__ == "__main__":
    print(f"Starting data collection at: {datetime.now(WIB)}")
    main()
    print(f"Process completed at: {datetime.now(WIB)}")