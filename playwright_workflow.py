"""Integrated Playwright workflow for OmniSight."""

import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from vision.vlm_analyzer import analyze_screenshot
from agent.action_engine import generate_fix_proposals
from agent.repair_engine import (
    apply_approved_css,
    capture_repaired_screenshot,
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
    approved_proposal_index: int | None = None,
) -> dict[str, Any]:
    """
    Execute shopping workflow, analyze UI, and optionally
    apply one explicitly approved CSS repair.
    """

    result: dict[str, Any] = {
        "success": False,
        "product_id": str(product_id),
        "steps": {},
        "final_url": None,
        "errors": [],
        "screenshots": [],
        "analysis": None,
        "action_engine": None,
        "repair": None,
        "post_repair_analysis": None,
    }

    browser = None
    page = None

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    def capture_screenshot(label: str) -> str | None:
        """Capture and record a screenshot."""

        if page is None:
            return None

        try:
            path = ARTIFACT_DIR / f"{label}.png"

            page.screenshot(
                path=str(path),
                full_page=True,
                timeout=10000,
            )

            result["screenshots"].append(str(path))

            logger.info("Screenshot saved: %s", path)

            return str(path)

        except PlaywrightError:
            logger.exception(
                "Screenshot capture failed: %s",
                label,
            )
            return None

    with sync_playwright() as playwright:

        try:
            browser = playwright.chromium.launch(
                headless=headless
            )

            page = browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 900,
                }
            )

            page.set_default_timeout(timeout_ms)

            # STEP 1: Open website.
            logger.info("Opening website: %s", base_url)

            page.goto(
                base_url,
                wait_until="commit",
                timeout=timeout_ms,
            )

            page.locator("body").wait_for(
                state="visible"
            )

            result["steps"]["website_opened"] = True

            # STEP 2: Open product page.
            product_selector = (
                f'[data-go="#/product/{product_id}"]'
            )

            product_link = page.locator(
                product_selector
            ).first

            try:
                product_link.wait_for(
                    state="visible"
                )

            except PlaywrightTimeoutError:
                logger.warning(
                    "Product not visible; retrying homepage."
                )

                page.goto(
                    base_url,
                    wait_until="commit",
                    timeout=timeout_ms,
                )

                product_link = page.locator(
                    product_selector
                ).first

                product_link.wait_for(
                    state="visible"
                )

            product_link.click()

            page.wait_for_url(
                f"**/product/{product_id}**"
            )

            result["steps"]["product_opened"] = True

            # STEP 3: Add product to cart.
            add_button = page.locator(
                f'button[data-add="{product_id}"]'
            ).first

            try:
                add_button.wait_for(
                    state="visible"
                )

                add_button.click()

            except PlaywrightTimeoutError:
                logger.warning(
                    "Retrying product route."
                )

                page.goto(
                    f"{base_url}/#/product/{product_id}",
                    wait_until="commit",
                    timeout=timeout_ms,
                )

                add_button = page.locator(
                    f'button[data-add="{product_id}"]'
                ).first

                add_button.wait_for(
                    state="visible"
                )

                add_button.click()

            result["steps"]["product_added"] = True

            # STEP 4: Open cart.
            cart_link = page.locator(
                'a[href="#/cart"]'
            ).first

            cart_link.wait_for(
                state="visible"
            )

            cart_link.click()

            page.wait_for_url("**/cart**")

            result["steps"]["cart_opened"] = True

            # STEP 5: Verify cart.
            cart_text = page.locator(
                "body"
            ).inner_text().lower()

            expected_product = (
                "classic light blue denim jacket"
            )

            if expected_product not in cart_text:
                raise AssertionError(
                    "Expected product was not found in cart."
                )

            if "items (1)" not in cart_text:
                raise AssertionError(
                    "Cart item count was not verified."
                )

            result["steps"]["cart_verified"] = True

            # STEP 6: Open checkout.
            checkout_button = page.locator(
                'button[data-go="#/checkout"]'
            ).first

            checkout_button.wait_for(
                state="visible"
            )

            checkout_button.click()

            page.wait_for_url("**/checkout**")

            result["steps"]["checkout_opened"] = True

            result["final_url"] = page.url
            result["success"] = True

            # STEP 7: Capture initial screenshot.
            before_path = capture_screenshot(
                "checkout_before_repair"
            )

            result["steps"]["before_screenshot_captured"] = (
                before_path is not None
            )

            # STEP 8: Analyze screenshot using Gemini.
            if before_path:

                try:
                    analysis = analyze_screenshot(
                        before_path,
                        viewport="desktop",
                    )

                    result["analysis"] = (
                        analysis.model_dump()
                    )

                    result["steps"]["gemini_analysis_completed"] = True

                    # STEP 9: Generate CSS proposals.
                    proposals = generate_fix_proposals(
                        analysis
                    )

                    result["action_engine"] = proposals

                    result["steps"]["proposals_generated"] = True

                    # STEP 10: Apply only explicitly approved proposal.
                    if approved_proposal_index is not None:

                        proposal_list = proposals.get(
                            "proposals",
                            [],
                        )

                        if (
                            approved_proposal_index < 0
                            or approved_proposal_index >= len(proposal_list)
                        ):
                            result["repair"] = {
                                "success": False,
                                "status": "rejected",
                                "message": "Invalid proposal index.",
                            }

                        else:
                            selected_proposal = proposal_list[
                                approved_proposal_index
                            ]

                            repair_result = apply_approved_css(
                                page,
                                selected_proposal,
                                approved=True,
                            )

                            result["repair"] = repair_result

                            if repair_result.get("success"):

                                result["steps"]["repair_applied"] = True

                                # STEP 11: Capture repaired screenshot.
                                after_result = capture_repaired_screenshot(
                                    page,
                                    str(
                                        ARTIFACT_DIR
                                        / "checkout_after_repair.png"
                                    ),
                                )

                                result["post_repair_screenshot"] = (
                                    after_result
                                )

                                if after_result.get("success"):

                                    result["screenshots"].append(
                                        after_result["screenshot"]
                                    )

                                    # STEP 12: Analyze again.
                                    try:
                                        after_analysis = analyze_screenshot(
                                            after_result["screenshot"],
                                            viewport="desktop",
                                        )

                                        result["post_repair_analysis"] = (
                                            after_analysis.model_dump()
                                        )

                                        result["steps"][
                                            "post_repair_analysis_completed"
                                        ] = True

                                    except Exception:
                                        logger.exception(
                                            "Post-repair analysis failed."
                                        )

                                        result["errors"].append(
                                            "Post-repair analysis failed."
                                        )

                except Exception:
                    logger.exception(
                        "Gemini analysis or proposal generation failed."
                    )

                    result["errors"].append(
                        "Screenshot analysis or proposal generation failed."
                    )

            logger.info(
                "Playwright workflow completed: %s",
                page.url,
            )

        except Exception as exc:

            message = (
                f"{type(exc).__name__}: {exc}"
            )

            logger.exception(
                "Playwright workflow failed."
            )

            result["errors"].append(message)

        finally:

            if browser is not None:

                try:
                    browser.close()

                    logger.info(
                        "Browser closed successfully."
                    )

                except PlaywrightError:
                    logger.exception(
                        "Browser cleanup failed."
                    )

    return result


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s %(levelname)s "
            "%(name)s: %(message)s"
        ),
    )

    print(run_playwright_workflow())
