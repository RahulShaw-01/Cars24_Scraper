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
                bigbox = soup.find_all('div', {'class': 'styles_wrapper__b4UUV'})
                if not bigbox:
                    break
                smallbox = bigbox[0].find_all('div', {'class': 'styles_contentWrap__9oSrl'})
                if not smallbox:
                    break
                for car_element in smallbox:
                    car_data = self.extract_car_info(car_element)
                    if car_data:
                        all_cars.append(car_data)
                time.sleep(1)
            except Exception:
                continue
        return all_cars

    def extract_car_info(self, car_element):
        try:
            name_element = car_element.find('span', {'class': 'sc-braxZu kjFjan'})
            if name_element:
                full_name = name_element.get_text().strip()
                year = full_name[:4] if len(full_name) >= 4 else "N/A"
                name = full_name[5:] if len(full_name) > 5 else full_name
            else:
                return None

            price_element = car_element.find('p', {'class': 'sc-braxZu cyPhJl'})
            price = price_element.get_text().strip() if price_element else 'N/A'

            location_element = car_element.find('p', {'class': 'sc-braxZu lmmumg'})
            location = location_element.get_text().strip() if location_element else 'N/A'
            location = ' '.join(location.split()) if location != 'N/A' else 'N/A'

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
        except Exception:
            return None

scraper = Car24Scraper()

@app.route('/')
def index():
    cities = ['Kolkata', 'Mumbai', 'Delhi NCR', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Ahmedabad', 'Surat', 'Jaipur',
              'New Delhi', 'Kochi', 'Nashik', 'Ludhiana', 'Chandigarh', 'Patna', 'Indore', 'Coimbatore', 'Ghaziabad',
              'Lucknow', 'Noida', 'Gurgaon', 'Nagpur', 'Rajkot', 'Vadodara', 'Agra', 'Chandigarh tricity']
    brands = ['All', 'Maruti', 'Hyundai', 'Tata', 'Honda', 'Mahindra', 'Ford', 'Toyota', 'KIA', 'Renault', 'Volkswagen']
    return render_template('index.html', cities=cities, brands=brands)

@app.route('/scrape', methods=['POST'])
def scrape_car():
    city = request.form.get('city')
    brand = request.form.get('brand')
    model = request.form.get('model')
    try:
        pages = int(request.form.get('pages', 1))
    except ValueError:
        pages = 1

    if not city or not brand:
        flash('Please select both city and brand!', 'error')
        return redirect(url_for('index'))

    if pages < 1 or pages > 10:
        flash('Pages must be between 1 and 10!', 'error')
        return redirect(url_for('index'))

    cars_data = scraper.scrape_cars(city, brand, pages, model)
    scraper.scraped_data = cars_data
    if not cars_data:
        flash('No cars found! Try different city/brand/model combination.', 'warning')
        return redirect(url_for('index'))

    total_cars = len(cars_data)
    avg_year = 0
    price_min = price_max = 0
    fuel_counts = {}

    if cars_data:
        years = []
        prices = []

        for car in cars_data:
            try:
                year = int(car['Year'])
                if year > 1990:
                    years.append(year)
            except:
                pass

            price_text = car['Price']
            if '₹' in price_text and 'lakh' in price_text:
                try:
                    price_num = float(price_text.replace('₹', '').replace('lakh', '').strip())
                    prices.append(price_num)
                except:
                    pass

            fuel = car['Fuel_Type']
            fuel_counts[fuel] = fuel_counts.get(fuel, 0) + 1

        if years:
            avg_year = sum(years) // len(years)
        if prices:
            price_min = min(prices)
            price_max = max(prices)

    stats = {
        'total_cars': total_cars,
        'avg_year': avg_year,
        'price_min': price_min,
        'price_max': price_max,
        'fuel_counts': fuel_counts,
        'city': city,
        'brand': brand,
        'pages': pages
    }

    flash(f'Successfully scraped {total_cars} cars!', 'success')
    return render_template('results.html', cars=cars_data, stats=stats)

@app.route('/export/excel')
def export_excel():
    if not scraper.scraped_data:
        flash('No data to export!', 'error')
        return redirect(url_for('index'))
    try:
        df = pd.DataFrame(scraper.scraped_data)
        excel_bytes = io.BytesIO()
        with pd.ExcelWriter(excel_bytes, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Car24_Data')

            workbook = writer.book
            worksheet = writer.sheets['Car24_Data']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        excel_bytes.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'cars24_data_{timestamp}.xlsx'
        return send_file(
            excel_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting Excel: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/clear')
def clear_data():
    scraper.scraped_data = []
    flash('Data cleared successfully!', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
