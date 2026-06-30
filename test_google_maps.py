from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time

# Start Chrome
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.maximize_window()

# Open Google Maps
driver.get("https://www.google.com/maps")

time.sleep(5)

# Search
search_box = driver.find_element(By.NAME, "q")
search_box.clear()
search_box.send_keys("Transport Companies Mumbai")
search_box.send_keys(Keys.ENTER)

print("Search Done")

# Wait for results
time.sleep(8)

# Find left panel
panel = driver.find_element(By.XPATH, '//div[@role="feed"]')

# Find all business links
cards = panel.find_elements(By.CSS_SELECTOR, 'a[href*="/place/"]')

print("Total Place Links:", len(cards))

# Open first business
cards[0].click()

print("Opening first business...")

time.sleep(8)

# Business Name
name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
# Rating
rating = driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']").text

# Address
address = driver.find_element(
    By.CSS_SELECTOR,
    'button[data-item-id="address"]'
).text

print("=" * 50)
print("Business Name :", name)
print("Rating        :", rating)
print("Address       :", address)
# Website
try:
    website = driver.find_element(
        By.CSS_SELECTOR,
        'a[data-item-id="authority"]'
    ).text
except Exception:
    website = "Not Available"

# Phone
try:
    phone = driver.find_element(
        By.CSS_SELECTOR,
        'button[data-item-id*="phone"]'
    ).text
except Exception:
    phone = "Not Available"

print("Website       :", website)
print("Phone         :", phone)

input("Press Enter to close...")

driver.quit()