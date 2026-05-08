import streamlit as st
from playwright.sync_api import sync_playwright
import subprocess
import re
import math

subprocess.run(["playwright", "install", "chromium"], check=False)

st.set_page_config(page_title="Repair Pricing Tool", page_icon="💸")

st.title("💸 Repair Pricing Tool")
st.write("Search MobileSentrix parts and calculate your sell price.")


def calculate_price(p):
    if 99 <= p <= 199:
        price = p + (p * 0.65) + 70
    else:
        price = p + (p * 1.15) + 70

    price = math.ceil(price / 5) * 5
    return round(price - 0.01, 2)


def scrape_mobilesentrix(search_term):
    device_url = f"https://www.mobilesentrix.com/search?q={search_term.replace(' ', '+')}"
    products = []
    search_words = search_term.lower().split()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = browser.new_page()
        page.set_default_timeout(60000)

        try:
            page.goto(device_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("body", timeout=60000)

            # Try product-card scraping first
            product_links = page.locator("a.product-item-link").all()

            for link in product_links:
                try:
                    name = link.inner_text().strip()
                    name_lower = name.lower()

                    if not all(word in name_lower for word in search_words):
                        continue

                    parent = link.locator("xpath=ancestor::li[contains(@class, 'product-item')]")
                    price_text = parent.locator(".price").first.inner_text().strip()

                    price_num = float(price_text.replace("$", "").replace(",", ""))

                    products.append({
                        "name": name,
                        "price": price_num,
                        "sell": calculate_price(price_num)
                    })

                except Exception:
                    pass

            # Fallback old text method
            if not products:
                page_text = page.text_content("body") or ""
                lines = page_text.splitlines()

                for i in range(len(lines) - 1):
                    name = lines[i].strip()
                    next_line = lines[i + 1].strip()

                    if re.match(r"^\$\d+\.\d{2}$", next_line):
                        name_lower = name.lower()

                        if all(word in name_lower for word in search_words):
                            price_num = float(next_line.replace("$", ""))

                            products.append({
                                "name": name,
                                "price": price_num,
                                "sell": calculate_price(price_num)
                            })

        finally:
            browser.close()

    products.sort(key=lambda x: x["price"])
    return products


with st.form("search_form"):
    search_term = st.text_input(
        "Enter part search",
        placeholder="ex: iPhone 15 Pro Max screen"
    )
    submitted = st.form_submit_button("Search")


if submitted:
    if not search_term.strip():
        st.warning("Type a part first.")
    else:
        with st.spinner("Searching parts..."):
            products = scrape_mobilesentrix(search_term)

        if not products:
            st.error("No valid products found. Try a simpler search like: iphone 15 pro max")
        else:
            best = products[0]

            st.success("Best option found!")

            st.subheader("🔥 Best Option")
            st.write(f"**Part:** {best['name']}")
            st.write(f"**Cost:** ${best['price']:.2f}")
            st.write(f"**Sell Price:** ${best['sell']:.2f}")

            st.subheader("All Matching Products")

            for product in products:
                with st.container(border=True):
                    st.write(f"**{product['name']}**")
                    st.write(f"Cost: ${product['price']:.2f}")
                    st.write(f"Sell: ${product['sell']:.2f}")
