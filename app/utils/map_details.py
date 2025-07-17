import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import geocoder
import folium
from folium import IFrame
from geopy.distance import geodesic


def get_doctor_links(city, speciality):
    # Setup Chrome options
    options = Options()
    options.headless = True  # Run in headless mode
    options.add_argument('--headless')  # Disable GPU acceleration
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Initialize WebDriver (make sure chromedriver is in your PATH or specify path)
    driver = webdriver.Chrome(options=options)
    links = []
    try:
        url = f"https://www.med.tn/doctor/{speciality}/{city}"
        driver.get(url)

        # Wait for the doctor cards to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "card-doctor-block    "))
        )

        # Extract doctor cards
        doctor_cards = driver.find_elements(By.CLASS_NAME, "card-doctor-block    ")
        
        for i, card in enumerate(doctor_cards, 1):
            links.append(card.find_element(By.TAG_NAME, 'a').get_attribute('href'))

    finally:
        driver.quit()
    return links



def extract_doctor_profile(url):
    # Headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Send request
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract profile label section
    profile = soup.find('div', class_='profile__label')
    if not profile:
        raise Exception("Profile section not found")

    # Extract image
    img_tag = soup.find('div', class_='profile__photo')
    img = ""
    if img_tag and img_tag.find('img'):
        img_src = img_tag.find('img')['src']
        img = img_src.replace(
            'https://imagecdn.med.ovh/unsafe/195x195/filters:format():quality(10):blur(30)/', '')

    # Extract name, speciality, city
    name = profile.find('h1').text.strip() if profile.find('h1') else ''
    speciality = profile.find('div', class_='profile__label--spe')
    speciality = speciality.text.strip() if speciality else ''
    city = profile.find('div', class_='profile__label--adr')
    city = city.text.strip() if city else ''

    # Extract address
    address_tag = soup.find('span', class_='profile__adr')
    address = address_tag.text.strip() if address_tag else ''

    # Extract phone numbers
    phone_numbers = []
    if soup.find('div', class_='displaynum'):
        num_tels = soup.find('div', class_='displaynum') 
        phone_numbers = [a.get_text(strip=True) for a in num_tels.find_all('a')]
        if phone_numbers[-1].startswith('Book'):
            phone_numbers.pop()
    else:
        phone_numbers = ['N/A']
    # Extract map position
    map_tag = soup.find('a', class_='btn-itineraire') or soup.find('a', target='_dir')
    map_position = ""
    if map_tag and 'href' in map_tag.attrs:
        map_position = map_tag['href'].replace('?api=1&destination=', '')

    # Final output
    full_details = {
        'img': img,
        'name': name,
        'speciality': speciality,
        'city': city,
        'address': address,
        'phone_numbers': phone_numbers,
        'map_position': map_position
    }
    return full_details

def get_my_location():
    g = geocoder.ip('me')
    if not g.ok or not g.latlng:
        raise RuntimeError("Unable to detect your location.")

    user_lat, user_lon = g.latlng
    city = g.city or "Your Location"
    country = g.country or ""
    return user_lat, user_lon, city, country

def create_the_map(speciality):

    # Get user location
    user_lat, user_lon, city, country = get_my_location()
    map = folium.Map(location=[user_lat, user_lon], zoom_start=12)
    folium.Marker(
        [user_lat, user_lon],
        popup=f"You are here: {city}, {country}",
        icon=folium.Icon(color='red', icon='user')
    ).add_to(map)

    # Fetch doctors
    all_docs = get_doctor_links(city.lower(), speciality.lower())

    for url in all_docs:
        try:
            doc = extract_doctor_profile(url)
            if not doc.get("map_position"):
                continue

            lat_str, lon_str = doc['map_position'].replace('https://www.google.com/maps/dir/','').split(',')
            lat, lon = float(lat_str), float(lon_str)

            # Calculate distance to user
            distance_km = geodesic((user_lat, user_lon), (lat, lon)).km
            if distance_km > 4:
                continue  # Skip doctors farther than 4km

            # Build popup
            img_html = f"<img src='{doc['img']}' width='100' height='100'><br>" if doc.get("img") else ""
            phone_html = "<br>".join(doc.get("phone_numbers", []))
            popup_html = f"""
            {img_html}
            <b>{doc['name']}</b><br>
            <i>{doc['speciality']}</i><br>
            <b>Address:</b> {doc['address']}<br>
            <b>Phone:</b><br>{phone_html}
            <br><b>Distance:</b> {distance_km:.2f} km
            """

            iframe = IFrame(popup_html, width=250, height=250)
            popup = folium.Popup(iframe, max_width=300)

            folium.Marker(
                [lat, lon],
                popup=popup,
                icon=folium.Icon(color='blue', icon='plus')
            ).add_to(map)

        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Save map
    map.save("map.html")