from flask import Flask, render_template, request, send_file, flash, url_for, redirect
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'car24_webscrapper_2585'

class Car24Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = []

    def scrape_cars(self, city, brand, pages=1, model=None):
        all_cars = []
        city_url = city.lower().replace(' ', '-')
        brand_url = brand.lower().replace(' ', '-')
        model_url = model.lower().replace(' ', '-') if model else ''

        for page in range(1, pages + 1):
            try:
                if brand_url == 'all':
                    url = f"https://www.cars24.com/buy-used-car-{city_url}/?page={page}"
                else:
                    if model_url:
                        url = f"https://www.cars24.com/buy-used-{brand_url}-{model_url}-cars-{city_url}/?page={page}"
                    else:
                        url = f"https://www.cars24.com/buy-used-{brand_url}-cars-{city_url}/?page={page}"

                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the "big box" container that holds all the car listings
                bigbox = soup.find('div', {'class': 'styles_wrapper__b4UUV'})
                
                if not bigbox:
                    print(f"No big box found on page {page}. Stopping.")
                    break
                
                # Find all "small box" containers, each representing a single car
                smallbox = bigbox.find_all('div', {'class': 'styles_contentWrap__9oSrl'})
                
                if not smallbox:
                    print(f"No small boxes found on page {page}. Stopping.")
                    break
                
                for car_element in smallbox:
                    car_data = self.extract_car_info(car_element)
                    if car_data:
                        all_cars.append(car_data)
                
                time.sleep(1)
            except Exception as e:
                print(f"An error occurred while scraping page {page}: {e}")
                continue
        return all_cars

    def extract_car_info(self, car_element):
        try:
            # Finding the car name and year using the provided class
            name_element = car_element.find('span', {'class': 'sc-braxZu kjFjan'})
            if name_element:
                full_name = name_element.get_text().strip()
                year = full_name[:4] if len(full_name) >= 4 else "N/A"
                name = full_name[5:] if len(full_name) > 5 else full_name
            else:
                return None

            # Finding the car price using the provided class
            price_element = car_element.find('p', {'class': 'sc-braxZu cyPhJl'})
            price = price_element.get_text().strip() if price_element else 'N/A'

            # Finding the location using the provided class
            location_element = car_element.find('p', {'class': 'sc-braxZu lmmumg'})
            location = location_element.get_text().strip() if location_element else 'N/A'
            location = ' '.join(location.split()) if location != 'N/A' else 'N/A'

            # Finding other details like KM driven, fuel type, etc., using the provided class
            detail_element = car_element.find_all('p', {'class': 'sc-braxZu kvfdZL'})
            km_driven = detail_element[0].get_text().strip() if len(detail_element) > 0 else 'N/A'
            fuel_type = detail_element[1].get_text().strip() if len(detail_element) > 1 else 'N/A'
            transmission = detail_element[2].get_text().strip() if len(detail_element) > 2 else 'N/A'

            return {
                'Car_Name': name,
                'Year': year,
                'Price': price,
                'Location': location,
                'KM_Driven': km_driven,
                'Fuel_Type': fuel_type,
                'Transmission': transmission,
                'Scraped_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"Error extracting car info: {e}")
            return None

# The rest of your Flask code remains unchanged and is not included here for brevity.