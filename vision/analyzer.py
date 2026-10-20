
from pathlib import Path

from PIL import Image, ImageChops


def check_horizontal_overflow(page):
    """Check whether page content exceeds the viewport width."""
    return page.evaluate("""
        () => {
            const viewportWidth = window.innerWidth;
            const documentWidth =
                document.documentElement.scrollWidth;

            return {
                viewport_width: viewportWidth,
                document_width: documentWidth,
                has_horizontal_overflow:
                    documentWidth > viewportWidth
            };
        }
    """)


def find_overflowing_elements(page):
    """Find visible elements extending beyond viewport horizontally."""
    return page.evaluate("""
        () => {
            const viewportWidth = window.innerWidth;

            return Array.from(document.querySelectorAll("body *"))
                .filter(element => {
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);

                    return style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        rect.width > 0 &&
                        (
                            rect.left < -1 ||
                            rect.right > viewportWidth + 1
                        );
                })
                .slice(0, 50)
                .map(element => {
                    const rect = element.getBoundingClientRect();

                    return {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || "",
                        class_name:
                            typeof element.className === "string"
                                ? element.className
                                : "",
                        left: Math.round(rect.left),
                        right: Math.round(rect.right)
                    };
                });
        }
    """)


def check_missing_elements(page, expected_selectors):
    """Find expected CSS selectors that are missing or hidden."""
    missing = []

    for selector in expected_selectors:
        try:
            locator = page.locator(selector).first

            if not locator.is_visible():
                missing.append(selector)

        except Exception:
            missing.append(selector)

    return missing



def compare_screenshots(first_path, second_path):
    """Compare screenshots and calculate the changed pixel ratio."""
    first_path = Path(first_path)
    second_path = Path(second_path)

    try:
        with Image.open(first_path) as image:
            first = image.convert("RGB")

        with Image.open(second_path) as image:
            second = image.convert("RGB")

        if first.size != second.size:
            return {
                "comparable": False,
                "error": "Screenshot dimensions do not match.",
                "first_size": first.size,
                "second_size": second.size,
            }

        difference = ImageChops.difference(first, second)
        changed_pixels = sum(
            value != 0
            for value in difference.convert("L").get_flattened_data()
        )

        total_pixels = first.width * first.height

        return {
            "comparable": True,
            "dimensions": first.size,
            "changed_pixels": changed_pixels,
            "changed_pixel_ratio": round(
                changed_pixels / total_pixels, 4
            ),
        }

    except (OSError, ValueError) as error:
        return {
            "comparable": False,
            "error": str(error),
        }


def analyze_page(page, expected_selectors=None):
    """Run responsive UI checks on an existing Playwright page."""
    report = {
        "horizontal_overflow": None,
        "overflowing_elements": [],
        "missing_elements": [],
        "errors": [],
    }

    try:
        report["horizontal_overflow"] = (
            check_horizontal_overflow(page)
        )
    except Exception as error:
        report["errors"].append(
            f"Horizontal overflow check failed: {error}"
        )

    try:
        report["overflowing_elements"] = (
            find_overflowing_elements(page)
        )
    except Exception as error:
        report["errors"].append(
            f"Element overflow check failed: {error}"
        )

    if expected_selectors:
        try:
            report["missing_elements"] = check_missing_elements(
                page, expected_selectors
            )
        except Exception as error:
            report["errors"].append(
                f"Missing element check failed: {error}"
            )

    return report