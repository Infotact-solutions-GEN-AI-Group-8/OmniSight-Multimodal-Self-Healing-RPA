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
