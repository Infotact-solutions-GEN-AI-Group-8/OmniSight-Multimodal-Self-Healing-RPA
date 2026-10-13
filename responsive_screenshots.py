
from pathlib import Path
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


def _validate_screenshot(path):
    """Return an error message if the screenshot file is invalid."""
    if not path.is_file():
        return "Screenshot file was not created."

    if path.stat().st_size == 0:
        return "Screenshot file is empty."

    try:
        with path.open("rb") as image_file:
            if image_file.read(8) != b"\x89PNG\r\n\x1a\n":
                return "Screenshot is not a valid PNG file."
    except OSError as error:
        return f"Could not validate screenshot: {error}"

    return None


def capture_responsive_screenshots(
    url=URL,
    output_dir=BASE_DIR,
    devices=None,
    headless=True,
):
    """Capture responsive pages and return screenshot paths and errors.

    Returns:
        {
            "screenshots": [successful screenshot path strings],
            "errors": [descriptions of failed captures or validations],
        }
    """
    results = {"screenshots": [], "errors": []}
    output_dir = Path(output_dir)
    devices = devices or DEVICES

    with sync_playwright() as playwright:
        browser = None

        try:
            browser = playwright.chromium.launch(headless=headless)

            for device_name, size in devices.items():
                page = None

                try:
                    page = browser.new_page(viewport=size)

                    # Capture homepage and product listing.
                    for page_name in ("homepage", "product_listing"):
                        path = output_dir / device_name / f"{page_name}.png"

                        try:
                            page.goto(
                                url + PAGES[page_name],
                                wait_until="networkidle",
                                timeout=60000,
                            )
                            path.parent.mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(path), full_page=True)

                            error = _validate_screenshot(path)
                            if error:
                                results["errors"].append(
                                    f"{device_name}/{page_name}: {error}"
                                )
                            else:
                                results["screenshots"].append(str(path))
                                print(f"SUCCESS: {path}")

                        except Exception as error:
                            results["errors"].append(
                                f"{device_name}/{page_name}: {error}"
                            )

                    # Add a product before capturing cart and checkout.
                    try:
                        page.goto(
                            url + PAGES["homepage"],
                            wait_until="networkidle",
                            timeout=60000,
                        )
                        add_button = page.get_by_role(
                            "button",
                            name="Add to cart",
                            exact=False,
                        ).first
                        add_button.wait_for(state="visible", timeout=15000)
                        add_button.click()
                        page.wait_for_timeout(1000)
                    except Exception as error:
                        results["errors"].append(
                            f"{device_name}/add_product_to_cart: {error}"
                        )
                        continue

                    for page_name in ("cart", "checkout"):
                        path = output_dir / device_name / f"{page_name}.png"

                        try:
                            page.goto(
                                url + PAGES[page_name],
                                wait_until="networkidle",
                                timeout=60000,
                            )
                            path.parent.mkdir(parents=True, exist_ok=True)
                            page.screenshot(path=str(path), full_page=True)

                            error = _validate_screenshot(path)
                            if error:
                                results["errors"].append(
                                    f"{device_name}/{page_name}: {error}"
                                )
                            else:
                                results["screenshots"].append(str(path))
                                print(f"SUCCESS: {path}")

                        except Exception as error:
                            results["errors"].append(
                                f"{device_name}/{page_name}: {error}"
                            )

                except Exception as error:
                    results["errors"].append(
                        f"{device_name}: {error}"
                    )
                finally:
                    if page is not None:
                        try:
                            page.close()
                        except Exception as error:
                            results["errors"].append(
                                f"{device_name}/close_page: {error}"
                            )

        except Exception as error:
            results["errors"].append(f"Browser startup: {error}")
        finally:
            if browser is not None:
                try:
                    browser.close()
                except Exception as error:
                    results["errors"].append(f"Browser close: {error}")

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