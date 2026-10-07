# OmniSight Architecture

## Overview

OmniSight follows a modular architecture where CI/CD events trigger the
backend, which coordinates browser automation, screenshot capture,
vision analysis, and AI-based self-healing.

## Components

### FastAPI

Receives CI/CD build events through the `/webhook` endpoint.

### Agent

Responsible for reasoning about failures and selecting recovery actions.

### Playwright

Responsible for browser interaction and RPA execution.

### Screenshot Module

Captures the current UI state at multiple viewport sizes.

### Vision

Analyzes screenshots and identifies UI elements or visual changes.

### Self-Healing

Uses the available UI information to recover failed automation actions.

## Data Flow

```text
CI/CD Event
    |
    v
FastAPI Webhook
    |
    v
Agent
    |
    +----> Playwright
    |
    +----> Screenshot
    |
    v
Vision Analysis
    |
    v
Failure Diagnosis
    |
    v
Recovery Decision
    |
    v
Playwright Action
    |
    v
Result