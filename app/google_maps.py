from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time
from app.models import Lead


def search_google_maps(keyword, category, group_name, db):

    print("Keyword :", keyword)
    print("Category:", category)
    print("Group   :", group_name)

    # Start Chrome
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install())
    )

    driver.maximize_window()

    # Open Google Maps
    driver.get("https://www.google.com/maps")

    time.sleep(5)

    # Search Box
    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(keyword)
    search_box.send_keys(Keys.ENTER)

    print("Searching Google Maps...")

    # Wait for results
    time.sleep(8)

    # Left panel
    panel = driver.find_element(By.XPATH, '//div[@role="feed"]')

    # Business links
    cards = panel.find_elements(
        By.CSS_SELECTOR,
        'a[href*="/place/"]'
    )

    print("=" * 50)
    print("Businesses Found:", len(cards))
    print("=" * 50)

    if len(cards) == 0:
        print("No businesses found.")
        input("Press Enter to close browser...")
        driver.quit()
        return

        # Open first business
    for i in range(min(10, len(cards))):

        # Reload cards every time
        panel = driver.find_element(By.XPATH, '//div[@role="feed"]')
        cards = panel.find_elements(
            By.CSS_SELECTOR,
            'a[href*="/place/"]'
        )

        cards[i].click()

        print(f"Opening Business {i+1}...")

        time.sleep(6)
        
        # ---------------- Business Name ----------------

        name = driver.find_element(
            By.CSS_SELECTOR,
            "h1.DUwDvf"
        ).text

        # ---------------- Rating ----------------

        try:
            rating = driver.find_element(
                By.CSS_SELECTOR,
                "div.F7nice span[aria-hidden='true']"
            ).text
        except:
            rating = "Not Available"

        # ---------------- Address ----------------

        try:
            address = driver.find_element(
                By.CSS_SELECTOR,
                'button[data-item-id="address"]'
            ).text.replace("", "").strip()
        except:
            address = "Not Available"


            # ---------------- Phone ----------------

        try:
            phone = driver.find_element(
            By.CSS_SELECTOR,
            'button[data-item-id^="phone"]'
        ).text.replace("", "").strip()
        except:
            phone = "Not Available"
 
        # ---------------- Website ----------------

        try:
            website = driver.find_element(
                By.CSS_SELECTOR,
                'a[data-item-id="authority"]'
            ).get_attribute("href")
        except:
            website = "Not Available"

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

            print(f"Business {i+1} saved successfully.")        
        