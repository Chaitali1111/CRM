from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from app.models import Lead


def search_google_maps(keyword, category, group_name, db):
    results = []

    print("Keyword :", keyword)
    print("Category:", category)
    print("Group   :", group_name)

    options = Options()
    options.binary_location = "/usr/bin/chromium"

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service("/usr/bin/chromedriver")

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.maximize_window()

    driver.get("https://www.google.com/maps")

    time.sleep(5)

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)

    print("Searching Google Maps...")

    wait = WebDriverWait(driver, 30)

    panel = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, '//div[@role="feed"]')
        )
    )

    cards = panel.find_elements(
        By.CSS_SELECTOR,
        'a[href*="/place/"]'
    )

    print("=" * 50)
    print("Businesses Found:", len(cards))
    print("=" * 50)

    if len(cards) == 0:
        print("No businesses found.")
        driver.quit()
        return

    # Demo: First business only
    cards[0].click()

    print("Opening Business...")

    time.sleep(6)

    name = driver.find_element(
        By.CSS_SELECTOR,
        "h1.DUwDvf"
    ).text

    try:
        rating = driver.find_element(
            By.CSS_SELECTOR,
            "div.F7nice span[aria-hidden='true']"
        ).text
    except:
        rating = "Not Available"

    try:
        address = driver.find_element(
            By.CSS_SELECTOR,
            'button[data-item-id="address"]'
        ).text.replace("", "").strip()
    except:
        address = "Not Available"

    try:
        phone = driver.find_element(
            By.CSS_SELECTOR,
            'button[data-item-id^="phone"]'
        ).text.replace("", "").strip()
    except:
        phone = "Not Available"

    try:
        website = driver.find_element(
            By.CSS_SELECTOR,
            'a[data-item-id="authority"]'
        ).get_attribute("href")
    except:
        website = "Not Available"
    
    results.append({
        "company_name": name,
        "phone": phone,
        "address": address,
        "website": website,
        "rating": rating
    })  

    print("=" * 60)


    print("Business Name :", name)
    print("Rating        :", rating)
    print("Address       :", address)
    print("Phone         :", phone)
    print("Website       :", website)
    print("=" * 60)

    existing = db.query(Lead).filter(
        Lead.company_name == name
    ).first()

    if existing:
        print(f"{name} already exists.")
    else:
        new_lead = Lead(
            company_name=name,
            mobile_number=phone,
            address=address,
            category=category,
            group_name=group_name,
            city="",
            website=website
        )

        db.add(new_lead)
        db.commit()

        print("Business saved successfully.")

    driver.quit()
    return results
