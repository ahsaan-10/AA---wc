# Milestone 3 Diagrams Guide

This guide describes the finalized Milestone 3 diagram pack prepared as a native `app.diagrams.net` file for the current AI Website Fabricator codebase.

Main editable file:

- [M3_DIAGRAMS.drawio](M3_DIAGRAMS.drawio)

The file is draw.io-native, opens directly in `https://app.diagrams.net`, and contains one clean page per report diagram.

## 1. Diagram Pack Scope

The pack now includes all nine diagrams requested for the Milestone 3 report update:

1. `Figure 1.1 - High-Level System Flow`
2. `Figure 5.1 - System Architecture (Five-Layer)`
3. `Figure 5.2 - Use Case Diagram`
4. `Figure 5.3 - Class / Module Diagram`
5. `Figure 5.4 - End-to-End Sequence Diagram`
6. `Figure 13.2 - Data Flow Diagram`
7. `Figure 13.3 - Entity Relationship Diagram`
8. `Figure 13.4 - Deployment and Runtime Diagram`
9. `Figure 13.5 - Connected Export Package Structure`

## 2. Page Names Inside The Draw.io File

The current page names inside [M3_DIAGRAMS.drawio](M3_DIAGRAMS.drawio) are:

1. `1. High-Level System Flow`
2. `2. System Architecture`
3. `3. Use Case Diagram`
4. `4. Class Module Diagram`
5. `5. End-to-End Sequence`
6. `6. Data Flow Diagram`
7. `7. Entity Relationship Diagram`
8. `8. Deployment and Runtime`
9. `9. Connected Export Package`

## 3. What Each Diagram Shows

### 3.1 High-Level System Flow

Shows the complete top-level pipeline:

- URL input
- clone engine
- local clone bundle
- save to project
- Smart Dynamic Conversion
- SiteSpec, models, records, and media
- admin usage
- public API and clone bridge
- connected export packaging

### 3.2 System Architecture

Shows the five runtime layers:

- Streamlit control layer
- clone and inference layer
- persistence layer
- Flask service layer
- React admin layer

### 3.3 Use Case Diagram

Shows the two main actors:

- `Operator`
- `Content Manager`

And the major system use cases they perform.

### 3.4 Class / Module Diagram

Shows the main code modules and their dependencies:

- `StreamlitApp`
- `CloneEngine`
- `SmartConversion`
- `FlaskService`
- `ConnectedExport`
- `ReactAdminApp`
- `Database`

### 3.5 End-to-End Sequence Diagram

Shows the time-ordered lifecycle of one site across:

- user actions
- Streamlit
- clone engine
- filesystem
- SQLite
- smart conversion
- Flask
- React admin

### 3.6 Data Flow Diagram

Shows how data transforms from cloned HTML into:

- `site_specs`
- `dynamic_models`
- `dynamic_records`
- `media_assets`

And how those outputs feed the admin panel and public APIs.

### 3.7 Entity Relationship Diagram

Shows the current Milestone 3 schema:

- `users`
- `cloned_sites`
- `conversion_blueprints`
- `site_specs`
- `dynamic_models`
- `dynamic_records`
- `media_assets`

### 3.8 Deployment and Runtime Diagram

Shows both runtime environments:

- main development runtime
- standalone connected export runtime

It includes:

- port `8501`
- port `5001`
- port `5010`
- database and filesystem resources

### 3.9 Connected Export Package Structure

Shows the standalone export folder layout:

- `connected_system/`
- `cloned_website/`
- `admin_system/`
- generated backend
- site-scoped database
- media
- generated dynamic artifacts

## 4. Design Rules Used

The pages were designed to stay clear and non-cluttered:

- one figure per page
- landscape canvas sized for report export
- consistent spacing and alignment
- orthogonal connectors for readability
- consistent color coding across all pages

Color logic:

- light blue: core application or clone pipeline blocks
- light pink: conversion or Flask service blocks
- light purple: admin-facing blocks
- light green: export or media/runtime packaging blocks
- light yellow: storage or primary entry blocks

## 5. Why This Pack Matches Milestone 3 Well

This diagram pack is based on the current working implementation, not outdated milestone assumptions. It reflects:

- the real Python + Streamlit + Flask + React stack
- the current SQLite schema
- the current `project_assets/` storage model
- the current connected export structure
- the real module names from the codebase

## 6. Editing Instructions

To edit any diagram:

1. Open [M3_DIAGRAMS.drawio](M3_DIAGRAMS.drawio) in `https://app.diagrams.net`.
2. Select the required page from the page tabs.
3. Adjust shapes, spacing, colors, or captions if needed.
4. Export the page as `PNG` or `SVG` for insertion into the report or PPT.

## 7. Current Status

The draw.io file has been validated as XML and currently contains all 9 required pages.
