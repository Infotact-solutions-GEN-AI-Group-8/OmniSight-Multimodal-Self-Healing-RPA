from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://omnisight-mock-website.vercel.app/"
BASE_DIR = Path("screenshots")

DEVICES = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}


def save_screenshot(page, device, name):
    folder = BASE_DIR / device
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"SUCCESS: {device}/{name}.png")


def add_product_to_cart(page):
    page.goto(URL + "#/", wait_until="networkidle", timeout=60000)

    add_button = page.get_by_role(
        "button", name="Add to cart", exact=False
    ).first

    add_button.wait_for(state="visible", timeout=15000)
    add_button.click()
    page.wait_for_timeout(1000)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            for device, size in DEVICES.items():
                page = browser.new_page(viewport=size)

                try:
                    page.goto(URL, wait_until="networkidle", timeout=60000)
                    save_screenshot(page, device, "homepage")
                    save_screenshot(page, device, "product_listing")

                    try:
                        add_product_to_cart(page)
                        page.goto(
                            URL + "#/cart",
                            wait_until="networkidle",
                            timeout=60000,
                        )
                        save_screenshot(page, device, "cart")

                        page.goto(
                            URL + "#/checkout",
                            wait_until="networkidle",
                            timeout=60000,
                        )
                        save_screenshot(page, device, "checkout")

                    except Exception as error:
                        print(f"ERROR: {device} cart/checkout: {error}")

                except Exception as error:
                    print(f"ERROR: {device}: {error}")
                finally:
                    page.close()
        finally:
            browser.close()

    print("Screenshot automation finished!")


if __name__ == "__main__":
    main()