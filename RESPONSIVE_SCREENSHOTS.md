
# Responsive Screenshot Capture

## Overview

The `responsive_screenshots.py` module provides a reusable
`capture_responsive_screenshots()` function for capturing and
validating responsive UI screenshots.

## Supported viewports

- Desktop: 1440 x 900
- Tablet: 768 x 1024
- Mobile: 390 x 844

## Captured pages

- Homepage
- Product listing
- Cart
- Checkout

Screenshots are saved under `screenshots/<device>/`.

## Usage

Run the capture script:

```powershell
python responsive_screenshots.py
```

Import the function without automatically launching a browser:

```python
from responsive_screenshots import capture_responsive_screenshots

results = capture_responsive_screenshots()
print(results["screenshots"])
print(results["errors"])
```

The result contains:
- `screenshots`: paths to validated PNG files.
- `errors`: capture, validation, or browser errors.

## Validation and error handling

The module checks that each screenshot exists, is non-empty,
and has a PNG file signature. Capture and browser errors are
collected in the returned result.

## Test results

- Responsive capture run: 12 screenshots validated successfully.
- Import safety check: passed; importing the module did not launch a browser.
- Unit tests: 2 passed.

## Notes and limitations

The homepage and product listing currently use the same website
route (`/#/`), so their screenshots may show the same content.
The cart and checkout captures depend on the website's available
routes and product-add workflow.