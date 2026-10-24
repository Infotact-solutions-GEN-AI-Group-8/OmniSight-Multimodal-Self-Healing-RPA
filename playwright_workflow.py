
"""Reusable Playwright workflow for the OmniSight mock shopping site."""

import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

BASE_URL = "https://omnisight-mock-website.vercel.app"
ARTIFACT_DIR = Path("artifacts/playwright")
DEFAULT_PRODUCT_ID = "41"

logger = logging.getLogger(__name__)


def run_playwright_workflow(
    product_id: str = DEFAULT_PRODUCT_ID,
    base_url: str = BASE_URL,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> dict[str, Any]:
    """Select a product, verify its cart, and navigate to checkout."""

    result: dict[str, Any] = {
        "success": False,
        "product_id": str(product_id),
        "steps": {},
        "final_url": None,
        "errors": [],
        "screenshots": [],
    }

    page = None
    browser = None

    def capture_failure(label: str) -> None:
        if page is None:
            return
        try:
            ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
            path = ARTIFACT_DIR / f"{label}.png"
            page.screenshot(
                path=str(path),
                full_page=True,
                timeout=5000,
            )
            result["screenshots"].append(str(path))
            logger.info("Failure screenshot saved: %s", path)
        except PlaywrightError:
            logger.exception("Could not capture screenshot: %s", label)

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.set_default_timeout(timeout_ms)

            logger.info("Opening website: %s", base_url)
            page.goto(
                base_url,
                wait_until="commit",
                timeout=timeout_ms,
            )
            page.locator("body").wait_for(state="visible")
            result["steps"]["website_opened"] = True

            # Open the product page.
            product_selector = f'[data-go="#/product/{product_id}"]'
            product_link = page.locator(product_selector).first

            try:
                product_link.wait_for(state="visible")
            except PlaywrightTimeoutError:
                logger.warning("Product not visible; retrying homepage")
                page.goto(
                    base_url,
                    wait_until="commit",
                    timeout=timeout_ms,
                )
                page.locator("body").wait_for(state="visible")
                product_link = page.locator(product_selector).first
                product_link.wait_for(state="visible")

            product_link.click()
            page.wait_for_url(f"**/product/{product_id}**")
            result["steps"]["product_opened"] = True

            # Add the product to the cart.
            add_button = page.locator(
                f'button[data-add="{product_id}"]'
            ).first

            try:
                add_button.wait_for(state="visible")
                add_button.click()
            except PlaywrightTimeoutError:
                logger.warning("Retrying product route")
                page.goto(
                    f"{base_url}/#/product/{product_id}",
                    wait_until="commit",
                    timeout=timeout_ms,
                )
                add_button = page.locator(
                    f'button[data-add="{product_id}"]'
                ).first
                add_button.wait_for(state="visible")
                add_button.click()

            result["steps"]["product_added"] = True

            # Open the cart.
            cart_link = page.locator('a[href="#/cart"]').first
            cart_link.wait_for(state="visible")
            cart_link.click()
            page.wait_for_url("**/cart**")
            result["steps"]["cart_opened"] = True

            # Verify the expected product and cart quantity.
            cart_text = page.locator("body").inner_text().lower()
            expected_product = "classic light blue denim jacket"

            if expected_product not in cart_text:
                raise AssertionError(
                    f"Product '{expected_product}' was not found in cart"
                )

            if "items (1)" not in cart_text:
                raise AssertionError("Cart item count was not verified")

            result["steps"]["cart_verified"] = True
            logger.info("Cart verified: %s", expected_product)

            # Proceed to checkout.
            checkout_button = page.locator(
                'button[data-go="#/checkout"]'
            ).first
            checkout_button.wait_for(state="visible")
            checkout_button.click()
            page.wait_for_url("**/checkout**")

            result["steps"]["checkout_opened"] = True
            result["final_url"] = page.url
            result["success"] = True
            logger.info("Workflow completed: %s", page.url)

        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            logger.exception("Playwright workflow failed")
            result["errors"].append(message)
            capture_failure("workflow_failure")

        finally:
            if browser is not None:
                try:
                    browser.close()
                    logger.info("Browser closed successfully")
                except PlaywrightError:
                    logger.exception("Browser cleanup failed")

    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    print(run_playwright_workflow())