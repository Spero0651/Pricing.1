from playwright.sync_api import sync_playwright
import re
import math


def calculate_price(p):
    if 99 <= p <= 199:
        price = p + (p * 0.65) + 70
    else:
        price = p + (p * 1.15) + 70

    price = math.ceil(price / 5) * 5
    return round(price - 0.01, 2)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    while True:
        search_term = input("\nEnter part search, or q to quit: ")

        if search_term.lower() in ["q", "quit", "exit"]:
            break

        device_url = f"https://www.mobilesentrix.com/search?q={search_term.replace(' ', '+')}"
        print("Searching:", device_url)

        page.goto(device_url)
        page.wait_for_load_state("networkidle")

        page_text = page.locator("body").inner_text()
        lines = page_text.splitlines()

        products = []
        search_words = search_term.lower().split()

        for i in range(len(lines)-1):
            name = lines[i].strip()
            next_line = lines[i + 1].strip()

            if re.match(r"^\$\d+\.\d{2}$", next_line):
                name_lower = name.lower()

                if all(word in name_lower for word in search_words):
                    price_num = float(next_line.replace("$", ""))

                    products.append({
                        "name": name,
                        "price": price_num
                    })

        if not products:
            print("No valid products found.")
        else:
            products.sort(key=lambda x: x["price"])

            best = products[0]
            sell_price = calculate_price(best["price"])

            print("\n🔥 BEST OPTION 🔥")
            print("----------------------")
            print("Part:", best["name"])
            print("Cost:", f"${best['price']}")
            print("Sell:", f"${sell_price}")

        again = input("\nSearch another part? y/n: ")
        if again.lower() != "y":
            break

    browser.close()
