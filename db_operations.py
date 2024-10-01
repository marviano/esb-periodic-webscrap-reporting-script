import mysql.connector
from datetime import datetime, timedelta
import random
import calendar

def connect_to_database():
    return mysql.connector.connect(
        host="182.253.188.171",
        user="dbadmin",
        password="Gfan2010!",
        database="hotways"
    )

def save_to_database(data):
    conn = connect_to_database()
    cursor = conn.cursor()

    for branch in ["Hotways Ponorogo", "Hotways Magelang", "Hotways Bojonegoro"]:
        offline_data = data.get(f"{branch} Offline", {})
        online_data = data.get(f"{branch} Online", {})

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
        """
        values = (
            branch.split()[-1],  # Extract branch name
            datetime.now().date(),
            offline_sales,
            online_sales,
            total_sales,
            total_pax,
            avg_sales_per_pax,
            num_bills,
            avg_sales_per_bill
        )

        cursor.execute(query, values)

    conn.commit()
    cursor.close()
    conn.close()
    print("Data saved to database successfully.")

def insert_test_data():
    conn = connect_to_database()
    cursor = conn.cursor()

    branches = ["Ponorogo", "Magelang", "Bojonegoro"]
    
    # Base values for each branch
    base_values = {
        "Ponorogo": {"offline": 1000000, "online": 500000, "pax": 100},
        "Magelang": {"offline": 1200000, "online": 600000, "pax": 120},
        "Bojonegoro": {"offline": 800000, "online": 400000, "pax": 80}
    }

    # Generate data for September and October
    for year, month in [(2024, 9), (2024, 10)]:
        _, days_in_month = calendar.monthrange(year, month)
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            
            for branch in branches:
                # Generate daily variations
                offline_variation = random.uniform(0.8, 1.2)  # 20% variation
                online_variation = random.uniform(0.8, 1.2)   # 20% variation
                pax_variation = random.uniform(0.9, 1.1)      # 10% variation

                # Apply weekend boost (assuming Saturday and Sunday are busier)
                if date.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
                    offline_variation *= 1.2
                    online_variation *= 1.2
                    pax_variation *= 1.2

                offline_sales = int(base_values[branch]["offline"] * offline_variation)
                online_sales = int(base_values[branch]["online"] * online_variation)
                total_sales = offline_sales + online_sales
                total_pax = max(1, int(base_values[branch]["pax"] * pax_variation))

                avg_sales_per_pax = total_sales / total_pax
                num_bills = int(total_pax * random.uniform(0.8, 1.2))  # Assume some bills have multiple pax
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

if __name__ == "__main__":
    insert_test_data()