from playwright.sync_api import sync_playwright
from pathlib import Path

URL = "https://omnisight-mock-website.vercel.app/"

BASE_DIR = Path("screenshots")

with sync_playwright() as p:
    browser = p.chromium.launch()

    devices = {
        "desktop": {
            "width": 1440,
            "height": 900
        },
        "tablet": {
            "width": 768,
            "height": 1024
        },
        "mobile": {
            "width": 390,
            "height": 844
        }
    }

    for device_name, size in devices.items():
        page = browser.new_page(
            viewport={
                "width": size["width"],
                "height": size["height"]
            }
        )

        page.goto(URL, wait_until="networkidle")

        output_folder = BASE_DIR / device_name
        output_folder.mkdir(parents=True, exist_ok=True)

        page.screenshot(
            path=str(output_folder / "homepage.png"),
            full_page=True
        )

        print(f"{device_name} screenshot saved")

        page.close()

    browser.close()

print("All responsive screenshots completed!")