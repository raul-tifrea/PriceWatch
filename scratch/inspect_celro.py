import httpx
from bs4 import BeautifulSoup

url = "https://www.cel.ro/laptop-apple-macbook-air-13-m1-8-core-cpu-7-core-gpu-8gb-256gb-space-grey-pNSQwPDYtPw-l/"
r = httpx.get(url, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
soup = BeautifulSoup(r.text, "lxml")

title = soup.select_one("h1.product-title, h1, h2.product-name, #product-name")
price = soup.select_one("span.price, #product-price, .productPrice")
img = soup.select_one("#main-product-image, .product-image img, a.magicat-zoom img")

print("Title:", title.text.strip() if title else "Not found")
print("Price content:", price.get('content') if price and price.has_attr('content') else (price.text.strip() if price else "Not found"))
print("Img:", img.get('src') if img else "Not found")

# Look at schema.org JSON-LD if present
import json
for script in soup.find_all('script', type='application/ld+json'):
    print("Found JSON-LD:")
    print(script.string[:200])
