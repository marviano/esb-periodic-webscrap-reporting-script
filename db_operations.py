import mysql.connector
from datetime import datetime, timezone, timedelta
import random
import calendar
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WIB = timezone(timedelta(hours=7))

def connect_to_database():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def data_exists_for_today(cursor, branch):
    query = "SELECT COUNT(*) FROM daily_sales WHERE branch = %s AND date = %s"
    cursor.execute(query, (branch, datetime.now(WIB).date()))
    count = cursor.fetchone()[0]
    return count > 0

def save_to_database(data):
    conn = connect_to_database()
    cursor = conn.cursor()

    try:
        for branch in ["Hotways Magelang", "Hotways Bojonegoro"]:
            offline_data = data.get(f"{branch} Offline", {})
            online_data = data.get(f"{branch} Online", {})

            branch_name = branch.split()[-1]
            current_date = datetime.now(WIB).date()

            offline_sales = float(offline_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
            online_sales = float(online_data.get('todayHighlightcurrentDailyGrossSales', '0').replace('.', '').replace(',', '.'))
            total_sales = offline_sales + online_sales

            total_pax = int(offline_data.get('todayHighlightPaxTotal', '0')) + int(online_data.get('todayHighlightPaxTotal', '0'))
            avg_sales_per_pax = float(offline_data.get('todayHighlightAverageNetSalesPerPax', '0').replace('.', '').replace(',', '.'))
            num_bills = int(offline_data.get('todayHighlightNumberOfBill', '0')) + int(online_data.get('todayHighlightNumberOfBill', '0'))
            avg_sales_per_bill = float(offline_data.get('todayHighlightAverageNetSalesPerBill', '0').replace('.', '').replace(',', '.'))

            query = """
            INSERT INTO daily_sales 
            (branch, date, offline_gross_sales, online_gross_sales, total_gross_sales, 
            total_pax, average_sales_per_pax, number_of_bills, average_sales_per_bill)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            offline_gross_sales = VALUES(offline_gross_sales),
            online_gross_sales = VALUES(online_gross_sales),
            total_gross_sales = VALUES(total_gross_sales),
            total_pax = VALUES(total_pax),
            average_sales_per_pax = VALUES(average_sales_per_pax),
            number_of_bills = VALUES(number_of_bills),
            average_sales_per_bill = VALUES(average_sales_per_bill)
            """
            values = (
                branch_name,
                current_date,
                offline_sales,
                online_sales,
                total_sales,
                total_pax,
                avg_sales_per_pax,
                num_bills,
                avg_sales_per_bill
            )

            try:
                cursor.execute(query, values)
                if cursor.rowcount == 1:
                    print(f"Inserted new data for {branch} on {current_date}")
                else:
                    print(f"Updated existing data for {branch} on {current_date}")
            except mysql.connector.Error as err:
                print(f"Error inserting/updating data for {branch}: {err}")

        conn.commit()
        print("All data committed to database successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def insert_test_data():
    conn = connect_to_database()
    cursor = conn.cursor()

    branches = ["Magelang", "Bojonegoro"]
    
    base_values = {
        "Magelang": {"offline": 1200000, "online": 600000, "pax": 120},
        "Bojonegoro": {"offline": 800000, "online": 400000, "pax": 80}
    }

    for year, month in [(2024, 9), (2024, 10)]:
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            
            for branch in branches:
                offline_variation = random.uniform(0.8, 1.2)
                online_variation = random.uniform(0.8, 1.2)
                pax_variation = random.uniform(0.9, 1.1)

                if date.weekday() >= 5:
                    offline_variation *= 1.2
                    online_variation *= 1.2
                    pax_variation *= 1.2

                offline_sales = int(base_values[branch]["offline"] * offline_variation)
                online_sales = int(base_values[branch]["online"] * online_variation)
                total_sales = offline_sales + online_sales
                total_pax = max(1, int(base_values[branch]["pax"] * pax_variation))

                avg_sales_per_pax = total_sales / total_pax
                num_bills = int(total_pax * random.uniform(0.8, 1.2))
                avg_sales_per_bill = total_sales / num_bills

                query = """
                INSERT INTO daily_sales 
                (branch, date, offline_gross_sales, online_gross_sales, total_gross_sales, 
                total_pax, average_sales_per_pax, number_of_bills, average_sales_per_bill)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                offline_gross_sales = VALUES(offline_gross_sales),
                online_gross_sales = VALUES(online_gross_sales),
                total_gross_sales = VALUES(total_gross_sales),
                total_pax = VALUES(total_pax),
                average_sales_per_pax = VALUES(average_sales_per_pax),
                number_of_bills = VALUES(number_of_bills),
                average_sales_per_bill = VALUES(average_sales_per_bill)
                """
                
                values = (
                    branch,
                    date,
                    offline_sales,
                    online_sales,
                    total_sales,
                    total_pax,
                    avg_sales_per_pax,
                    num_bills,
                    avg_sales_per_bill
                )

                try:
                    cursor.execute(query, values)
                    print(f"Inserted/Updated data for {branch} on {date}")
                except mysql.connector.Error as err:
                    print(f"Error inserting data for {branch} on {date}: {err}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Test data for September and October inserted successfully.")

# if __name__ == "__main__":
    # insert_test_data()