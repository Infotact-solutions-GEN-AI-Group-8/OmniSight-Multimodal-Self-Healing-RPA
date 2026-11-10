
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
from agent.verification import verify_repair


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
        "post_repair_screenshot": None,
        "verification": None,
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

            # Hide the temporary toast notification before screenshot.
            try:
                toast = page.locator("#toast")

                if toast.count() > 0:
                    toast.evaluate(
                        """
                        element => {
                            element.style.visibility = "hidden";
                        }
                        """
                    )

                    # Wait for the browser to apply the style.
                    page.wait_for_timeout(300)

            except PlaywrightError:
                logger.warning(
                    "Could not hide toast notification."
                )

            page.screenshot(
                path=str(path),
                full_page=True,
                timeout=10000,
            )

            result["screenshots"].append(str(path))

            logger.info(
                "Screenshot saved: %s",
                path,
            )

            return str(path)

        except PlaywrightError:
            logger.exception(
                "Screenshot capture failed: %s",
                label,
            )
            return None

    with sync_playwright() as playwright:

        try:
            # STEP 1: Launch browser.
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

            # STEP 2: Open website.
            logger.info(
                "Opening website: %s",
                base_url,
            )

            page.goto(
                base_url,
                wait_until="commit",
                timeout=timeout_ms,
            )

            page.locator("body").wait_for(
                state="visible"
            )

            result["steps"]["website_opened"] = True

            # STEP 3: Open product page.
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

            # STEP 4: Add product to cart.
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

            # STEP 5: Open cart.
            cart_link = page.locator(
                'a[href="#/cart"]'
            ).first

            cart_link.wait_for(
                state="visible"
            )

            cart_link.click()

            page.wait_for_url("**/cart**")

            result["steps"]["cart_opened"] = True

            # STEP 6: Verify cart.
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

            if "cart" not in cart_text:
                raise AssertionError(
                    "Cart was not verified."
                )

            result["steps"]["cart_verified"] = True

            # STEP 7: Open checkout.
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

            # STEP 8: Capture initial screenshot.
            before_path = capture_screenshot(
                "checkout_before_repair"
            )

            result["steps"]["before_screenshot_captured"] = (
                before_path is not None
            )

            # STEP 9: Analyze screenshot using Gemini.
            if before_path:

                try:
                    analysis = analyze_screenshot(
                        before_path,
                        viewport="desktop",
                    )

                    result["analysis"] = (
                        analysis.model_dump()
                    )

                    result["steps"][
                        "gemini_analysis_completed"
                    ] = True

                    # STEP 10: Generate CSS proposals.
                    proposals = generate_fix_proposals(
                        analysis
                    )

                    result["action_engine"] = proposals

                    result["steps"][
                        "proposals_generated"
                    ] = True

                    proposal_list = proposals.get(
                        "proposals",
                        [],
                    )

                    # STEP 11: Apply only explicitly approved proposal.
                    if approved_proposal_index is not None:

                        # Case 1: Gemini found no repair proposal.
                        if not proposal_list:

                            result["repair"] = {
                                "success": False,
                                "status": "skipped",
                                "message": (
                                    "No repair proposal available. "
                                    "Gemini did not detect a visible defect."
                                ),
                            }

                            logger.info(
                                "Repair skipped: no proposals available."
                            )

                        # Case 2: Invalid proposal index.
                        elif (
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

                            # Case 3: Manual review required.
                            if (
                                selected_proposal.get("status")
                                == "needs_manual_review"
                            ):

                                result["repair"] = {
                                    "success": False,
                                    "status": "skipped",
                                    "message": (
                                        "Proposal needs manual review. "
                                        "No automatic repair applied."
                                    ),
                                }

                            # Case 4: Apply approved CSS repair.
                            else:

                                repair_result = apply_approved_css(
                                    page,
                                    selected_proposal,
                                    approved=True,
                                )

                                result["repair"] = repair_result

                                if repair_result.get("success"):

                                    result["steps"][
                                        "repair_applied"
                                    ] = True

                                    logger.info(
                                        "Approved CSS repair applied."
                                    )

                                    # STEP 12: Capture repaired screenshot.
                                    after_result = (
                                        capture_repaired_screenshot(
                                            page,
                                            str(
                                                ARTIFACT_DIR
                                                / "checkout_after_repair.png"
                                            ),
                                        )
                                    )

                                    result[
                                        "post_repair_screenshot"
                                    ] = after_result

                                    if after_result.get("success"):

                                        result["screenshots"].append(
                                            after_result["screenshot"]
                                        )

                                        # STEP 13: Analyze repaired UI.
                                        try:
                                            after_analysis = (
                                                analyze_screenshot(
                                                    after_result["screenshot"],
                                                    viewport="desktop",
                                                )
                                            )

                                            result[
                                                "post_repair_analysis"
                                            ] = (
                                                after_analysis.model_dump()
                                            )

                                            result["steps"][
                                                "post_repair_analysis_completed"
                                            ] = True

                                            # STEP 14: Verify repair.
                                            verification = verify_repair(
                                                analysis,
                                                after_analysis,
                                            )

                                            result[
                                                "verification"
                                            ] = verification

                                            result["steps"][
                                                "repair_verification_completed"
                                            ] = True

                                            logger.info(
                                                "Repair verification completed."
                                            )

                                        except Exception:

                                            logger.exception(
                                                "Post-repair analysis failed."
                                            )

                                            result["errors"].append(
                                                "Post-repair analysis failed."
                                            )

                                    else:

                                        logger.warning(
                                            "Repaired screenshot capture failed."
                                        )

                    logger.info(
                        "Gemini analysis and proposal generation completed."
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

    print(
        run_playwright_workflow(
            approved_proposal_index=0
        )
    )