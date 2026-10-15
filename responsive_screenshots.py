
from pathlib import Path
import struct

from playwright.sync_api import sync_playwright

URL = "https://omnisight-mock-website.vercel.app/"
BASE_DIR = Path("screenshots")

DEVICES = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}

PAGES = {
    "homepage": "/#/",
    "product_listing": "/#/",
    "cart": "/#/cart",
    "checkout": "/#/checkout",
}


def _validate_screenshot(path, expected_size=None):
    """Validate PNG signature and optionally verify its dimensions."""
    path = Path(path)

    if not path.is_file():
        return "Screenshot file was not created."

    if path.stat().st_size == 0:
        return "Screenshot file is empty."

    try:
        with path.open("rb") as image_file:
            header = image_file.read(24)

        if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            return "Screenshot is not a valid PNG file."

        width, height = struct.unpack(">II", header[16:24])

        if width <= 0 or height <= 0:
            return "Screenshot has invalid dimensions."

        if expected_size and (width, height) != tuple(expected_size):
            return (
                f"Dimensions mismatch: expected {tuple(expected_size)}, "
                f"got {(width, height)}."
            )

    except OSError as error:
        return f"Could not validate screenshot: {error}"

    return None


def _capture_page(page, output_dir, device_name, page_name, results, url=URL):
    """Navigate to a configured route and capture a validated screenshot."""
    path = Path(output_dir) / device_name / f"{page_name}.png"

    try:
        target_url = url.rstrip("/") + PAGES[page_name]
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        page.locator("body").wait_for(state="visible", timeout=15000)

        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)

        error = _validate_screenshot(path)
        if error:
            results["errors"].append(f"{device_name}/{page_name}: {error}")
        else:
            results["screenshots"].append(str(path))
            print(f"SUCCESS: {path}")

    except Exception as error:
        results["errors"].append(f"{device_name}/{page_name}: {error}")


def add_product_to_cart(page, url=URL):
    """Add a product and verify that the cart is not empty."""
    page.goto(
        url.rstrip("/") + PAGES["homepage"],
        wait_until="domcontentloaded",
        timeout=60000,
    )

    add_button = page.get_by_role(
        "button", name="Add to cart", exact=False
    ).first
    add_button.wait_for(state="visible", timeout=15000)
    add_button.click()

    page.goto(
        url.rstrip("/") + PAGES["cart"],
        wait_until="domcontentloaded",
        timeout=60000,
    )
    page.locator("body").wait_for(state="visible", timeout=15000)

    body_text = page.locator("body").inner_text().lower()
    empty_messages = ("empty cart", "cart is empty", "your cart is empty")

    if any(message in body_text for message in empty_messages):
        raise RuntimeError("Product was not confirmed in the cart.")


def capture_responsive_screenshots(
    url=URL,
    output_dir=BASE_DIR,
    devices=None,
    headless=True,
):
    """Capture screenshots and return successful paths and errors."""
    results = {"screenshots": [], "errors": []}
    output_dir = Path(output_dir)
    devices = DEVICES if devices is None else devices

    if not devices:
        return results

    try:
        with sync_playwright() as playwright:
            browser = None
            try:
                browser = playwright.chromium.launch(headless=headless)

                for device_name, size in devices.items():
                    page = None
                    try:
                        page = browser.new_page(viewport=size)

                        for page_name in ("homepage", "product_listing"):
                            _capture_page(
                                page, output_dir, device_name,
                                page_name, results, url=url
                            )

                        try:
                            add_product_to_cart(page, url=url)
                        except Exception as error:
                            results["errors"].append(
                                f"{device_name}/add_product_to_cart: {error}"
                            )
                            continue

                        for page_name in ("cart", "checkout"):
                            _capture_page(
                                page, output_dir, device_name,
                                page_name, results, url=url
                            )

                    except Exception as error:
                        results["errors"].append(f"{device_name}: {error}")

                    finally:
                        if page is not None:
                            try:
                                page.close()
                            except Exception as error:
                                results["errors"].append(
                                    f"{device_name}/close_page: {error}"
                                )

            finally:
                if browser is not None:
                    browser.close()

    except Exception as error:
        results["errors"].append(f"Browser startup: {error}")

    return results


def main():
    results = capture_responsive_screenshots()

    print(f"\nValid screenshots: {len(results['screenshots'])}")

    if results["errors"]:
        print(f"Errors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"ERROR: {error}")
    else:
        print("All screenshots captured and validated successfully.")


if __name__ == "__main__":
    main()