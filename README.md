# OmniSight: Multimodal UI Self-Healing & RPA Agent

OmniSight is a multimodal AI-powered UI self-healing and autonomous RPA
agent designed to detect UI automation failures, analyze the affected
interface, and recover automation workflows automatically.

## Problem Statement

Traditional RPA and browser automation systems are highly dependent on
fixed selectors, element IDs, and predefined UI structures.

When a website changes its UI, automation scripts can fail.

OmniSight aims to make UI automation more resilient by combining:

- Browser automation
- Responsive UI screenshots
- Vision-based UI analysis
- Multimodal AI
- Agent-based reasoning
- Self-healing automation
- CI/CD integration

## Project Objective

The objective of OmniSight is to detect automation failures, understand
the current UI state, identify the changed or missing UI element, and
select an appropriate recovery action.

## System Architecture

```text
                    CI/CD Pipeline
                          |
                          v
                  +---------------+
                  | FastAPI Webhook|
                  +-------+-------+
                          |
                          v
                  +---------------+
                  |  Agent Layer  |
                  |  AI Reasoning |
                  +-------+-------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
      +---------------+       +---------------+
      |  Playwright   |       |  Screenshot   |
      |  Automation   |       |    Module     |
      +-------+-------+       +-------+-------+
              |                       |
              +-----------+-----------+
                          |
                          v
                  +---------------+
                  | Vision / VLM  |
                  | UI Analysis   |
                  +-------+-------+
                          |
                          v
                  +---------------+
                  | Self-Healing  |
                  |    Action     |
                  +-------+-------+
                          |
                          v
                  Updated Automation


## Responsive Screenshot Capture

The responsive screenshot module captures and validates screenshots for
four application routes across desktop, tablet, and mobile viewports.

### Viewport sizes

| Device | Width | Height |
|---|---:|---:|
| Desktop | 1440 | 900 |
| Tablet | 768 | 1024 |
| Mobile | 390 | 844 |

### Screenshot locations

Screenshots are organized by device:

- `screenshots/desktop/`
- `screenshots/tablet/`
- `screenshots/mobile/`

Each device folder contains screenshots for the homepage, product listing,
cart, and checkout routes.

### Run screenshot capture

Activate your Python virtual environment, then run:

```powershell
python .\responsive_screenshots.py
```

The script reports successful captures and validates the generated
screenshots.

## Responsive UI Analyzer

The module `vision/analyzer.py` provides these checks:

- Detect horizontal overflow beyond the viewport.
- Identify visible elements extending outside the viewport.
- Check whether expected CSS selectors are missing or hidden.
- Compare screenshots and calculate the changed-pixel ratio.
- Return structured error information when screenshot comparison fails.

The analyzer works with an existing Playwright page; importing the module
does not automatically launch a browser.

## Running Tests

Run the test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

The tests cover screenshot comparison, invalid or missing images,
dimension mismatches, overflow analysis, and screenshot capture validation.