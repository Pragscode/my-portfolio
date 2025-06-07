import requests
import time
from bs4 import BeautifulSoup
import csv
import os
import re
import mysql.connector
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.1mg.com/drugs-all-medicines?page={page}&label={alphabet}"
all_data = []
BATCH_SIZE = 1000
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def csv_maker(data, filename="details_products2.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "price", "description", "marketer_name", "salt_composition", "storage", "product_introduction", "side_effects"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Pa@29042007",
            database="demo"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def insert_into_database(connection, data):
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO medicines (name, price, description, marketer_name, salt_composition, storage, product_introduction, side_effects)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, [
            (
                item["name"], item["price"], item["description"], item["marketer_name"],
                item["salt_composition"], item["storage"], item["product_introduction"], item["side_effects"]
            ) for item in data
        ])
        connection.commit()
        print(f"Inserted {cursor.rowcount} records into the database.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")

def scrape_product_details(product_url):
    try:
        req = requests.get(product_url, headers=HEADERS, timeout=10)
        time.sleep(1)
        if req.status_code != 200:
            print(f"Failed to fetch {product_url} (Status: {req.status_code})")
            return {"marketer_name": "No details", "salt_composition": "No details", "storage": "No details", "product_introduction": "No details", "side_effects": "No details"}

        soup = BeautifulSoup(req.text, "lxml")

        marketer_div = soup.find("div", class_="DrugHeader__meta-value___vqYM0")
        marketer_name = marketer_div.text.strip() if marketer_div else "No details"

        salt_composition = "No details"
        storage = "No details"
        salt_composition_divs = soup.find_all("div", class_="saltInfo DrugHeader__meta-value___vqYM0")
        if len(salt_composition_divs) > 0:
            salt_composition = salt_composition_divs[0].text.strip()
        if len(salt_composition_divs) > 1:
            storage = salt_composition_divs[1].text.strip()

        product_introduction_div = soup.find("div", class_="DrugPane__content___3-yrB")
        product_introduction = product_introduction_div.text.strip() if product_introduction_div else "No details"

        side_effects_div = soup.find("div", class_="DrugOverview__list-container___2eAr6 DrugOverview__content___22ZBX")
        side_effects = '|'.join([effect.text.strip() for effect in side_effects_div.find_all("li")]) if side_effects_div else "No details"
        
        return {
            "marketer_name": marketer_name,
            "salt_composition": salt_composition,
            "storage": storage,
            "product_introduction": product_introduction,
            "side_effects": side_effects
        }

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {"marketer_name": "No details", "salt_composition": "No details", "storage": "No details", "product_introduction": "No details", "side_effects": "No details"}

db_connection = connect_to_database()
if not db_connection:
    print("Failed to connect to the database. Exiting.")
    exit()

for alphabet in 'abcdefghijklmnopqrstuvwxyz':
    page = 1

    while True:
        url = BASE_URL.format(page=page, alphabet=alphabet)
        print(f"Scraping: {url}")

        try:
            req = requests.get(url, headers=HEADERS, timeout=10)
            time.sleep(2)

            if req.status_code != 200:
                print(f"Failed to fetch {url} (Status: {req.status_code})")
                break

            soup = BeautifulSoup(req.text, "lxml")
            medicine_divs = soup.find_all("div", class_="style__width-100p___2woP5 style__flex-row___m8FHw")

            if not medicine_divs:
                print(f"No more medicines for '{alphabet.upper()}'. Moving to next letter.")
                break

            product_infos = []

            for div in medicine_divs:
                mg_all_data = div.find("a", class_="style__product-name___HASYw")
                if not mg_all_data:
                    continue

                product_url = "https://www.1mg.com" + mg_all_data.get("href")
                full_data = mg_all_data.text.strip()

                name_match = re.search(r'^[^\d]+', full_data)
                name = name_match.group(0).strip() if name_match else "No name"
                name = re.sub(r'MRP.*', '', name).strip()

                price_match = re.search(r'₹\d+(\.\d+)?', full_data)
                price = price_match.group(0).replace('₹', '') if price_match else "No price"

                description_start = full_data.find(price_match.group(0)) + len(price_match.group(0)) if price_match else 0
                description = full_data[description_start:].strip() if description_start else "No description"

                product_infos.append({
                    'name': name,
                    'price': price,
                    'description': description,
                    'product_url': product_url
                })

            with ThreadPoolExecutor(max_workers=30) as executor:
                future_to_product = {executor.submit(scrape_product_details, p["product_url"]): p for p in product_infos}

                for future in as_completed(future_to_product):
                    product = future_to_product[future]
                    try:
                        details = future.result()
                    except Exception as exc:
                        print(f"Error fetching details for {product['name']}: {exc}")
                        details = {"marketer_name": "No details", "salt_composition": "No details", "storage": "No details", "product_introduction": "No details", "side_effects": "No details"}

                  
                    product["description"] = re.sub(rf'{re.escape(details["marketer_name"])}|{re.escape(details["salt_composition"])}', '', product["description"]).strip()

                    obj = {
                        'name': product['name'],
                        'price': product['price'],
                        'description': product['description'],
                        'marketer_name': details["marketer_name"],
                        'salt_composition': details["salt_composition"],
                        'storage': details["storage"],
                        'product_introduction': details["product_introduction"],
                        'side_effects': details["side_effects"]
                    }

                    print(obj)
                    all_data.append(obj)

                    if len(all_data) >= BATCH_SIZE:
                        print(f"Saving {len(all_data)}")
                        csv_maker(all_data)
                        insert_into_database(db_connection, all_data)
                        all_data = []

            page += 1
            if page > 340:
                print(f"Finished scraping for '{alphabet.upper()}'")
                break

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break

if all_data:
    print(f"Saving final {len(all_data)}")
    csv_maker(all_data)
    insert_into_database(db_connection, all_data)

db_connection.close()
print("Scraping completed.")
