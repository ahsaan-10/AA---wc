# StreamClone
## Milestone 3 Updated Report Draft

This document is an M3-updated report source for the StreamClone project. It is designed to extend the older POC/Milestone 2 report into a Milestone 3 submission using the current working codebase as the source of truth.

It keeps the overall chapter flow of the previous report and adds the missing Milestone 3 material, especially:

- `Chapter 7: Implementation`
- `Chapter 8: Testing`
- updated `Achievements`
- updated `Appendices`
- updated `References`
- updated `Component`, `Deployment`, and `Operational` diagrams

Related project files:

- [AI_WEBSITE_FABRICATOR_MASTER_DOCUMENTATION.md](../MASTER_DOCUMENTATION.md)
- [M3_DIAGRAMS_GUIDE.md](../diagrams/DIAGRAMS_GUIDE.md)
- [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)

---

# CHAPTER 1
# INTRODUCTION

## 1.1 Background

Modern websites are often visually rich but difficult to reproduce, manage, and evolve without direct access to their original source code or design system. In many practical situations, teams need to study, clone, prototype, or restructure an existing website while preserving its look and feel. Traditional manual recreation is slow and error-prone, while purely generative approaches often fail to preserve exact layout, media behavior, and structure.

StreamClone addresses this gap by providing a deterministic website re-engineering workflow. Rather than attempting to imagine how a website should be rebuilt, the system clones the actual site structure, localizes important resources, preserves browsable output, and then builds an editable management layer on top of the cloned website.

The project has now evolved beyond a simple cloning proof of concept. In its current state, it supports:

- website cloning
- staged preview and saved clone packages
- raw HTML editing
- drag-and-drop editing
- dynamic content inference
- `SiteSpec` generation
- separate admin website generation
- public content APIs
- portable connected export packages

## 1.2 Motivation

The motivation for StreamClone comes from recurring real-world development problems:

- recreating existing sites manually takes too much time
- front-end fidelity is often lost in manual rebuilds
- external assets and relative references break when a site is copied incorrectly
- visual editing and structured content editing are usually split across unrelated tools
- static websites become difficult to maintain when content changes frequently

StreamClone was therefore developed as a bridge between static website capture and structured website management.

## 1.3 Objectives

The main objectives of the project are:

1. Clone and preserve the structure of a target website.
2. Allow technical users to edit the cloned HTML directly.
3. Allow non-technical users to manage structured content through a separate admin panel.
4. Generate a site-specific content model automatically from the clone.
5. Localize and manage media through a dedicated media pipeline.
6. Provide portable export packaging for standalone execution.

## 1.4 System Diagram

The project’s high-level system flow is:

`User -> Streamlit Control App -> Clone Engine -> Saved Clone -> Smart Dynamic Conversion -> Flask APIs + React Admin -> Connected Export`

Suggested insertion:

- Insert a general system diagram here if needed for continuity with the earlier report.
- For Milestone 3 grading, the diagram pack required by the guideline is already prepared separately in [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio).

---

# CHAPTER 2
# LITERATURE REVIEW & THE STRATEGIC PIVOT

## 2.1 Generative AI Approaches to Web Development

Many recent systems attempt to reproduce websites using generative AI or screenshot-to-code workflows. While these methods appear fast in demonstrations, they typically suffer from structural hallucination, inconsistent layout recreation, and unreliable component mapping.

## 2.2 The Hallucination Problem

Generative systems frequently:

- invent non-existent HTML structures
- omit real media and CSS dependencies
- break navigation behavior
- fail to preserve exact spacing and asset relationships

For a project that needs correctness, editability, and deployment realism, this is a major limitation.

## 2.3 Deterministic Cloning as a Reliable Alternative

The current StreamClone implementation follows a deterministic strategy. Instead of generating a guessed website, it:

- requests and crawls real pages
- captures navigable HTML pages
- downloads or rewrites assets
- preserves actual content references
- stores the resulting structure for later editing and management

This makes the platform much more suitable for academic demonstration and milestone-based validation.

## 2.4 Strategic Pivot

The project’s major architectural pivot is that it is no longer just a clone viewer. It is now a local website re-engineering platform with:

- preserved static clone bundles
- conversion into structured dynamic resources
- a separate site-scoped CMS
- exportable connected deployment

This pivot is essential to understanding Milestone 3, because M3 is where the project becomes a usable application rather than only a clone proof of concept.

---

# CHAPTER 3
# AIM & PROBLEM STATEMENT

## 3.1 Problem Definition

The central problem is:

`How can an existing static website be cloned, preserved, edited, and transformed into a manageable dynamic system without rebuilding the entire frontend manually?`

## 3.2 Specific Challenges Addressed

The project addresses the following challenges:

- preserving structure and navigation of a target website
- handling linked assets and rewriting broken paths
- maintaining editability after cloning
- inferring content models automatically
- supporting both technical and non-technical editing workflows
- packaging the system for independent running

## 3.3 Project Scope

### In Scope

- multi-page website cloning
- clone preview and saved project storage
- raw HTML code editing
- drag-and-drop editing
- rules-first site type and content inference
- dynamic record generation
- separate admin panel
- media management
- portable connected export

### Out of Scope

- enterprise-grade multi-user permission systems
- deep AI semantic reasoning over arbitrary JS applications
- cloud-scale database and deployment architecture
- perfect reconstruction of extremely dynamic SPA applications

---

# CHAPTER 4
# SYSTEM REQUIREMENTS

## 4.1 Technology Stack

### Backend and orchestration

- Python
- Streamlit
- Flask
- Flask-CORS
- requests
- BeautifulSoup4
- sqlite3
- itsdangerous

### Frontend

- React
- TypeScript
- Vite
- React Router

### Data and storage

- SQLite database: `users.db`
- local filesystem storage under `project_assets/`

## 4.2 Hardware Requirements

The project is intended to run on a normal development machine with:

- Windows environment
- Python runtime
- Node-compatible frontend build environment
- sufficient storage for clone bundles, media, and exported packages

## 4.3 Functional Requirements

The system shall:

- register and authenticate users
- clone and preview target websites
- save clone bundles persistently
- allow raw HTML editing
- allow drag-and-drop editing
- infer website type and structured resources
- generate `SiteSpec`
- generate seeded dynamic records
- expose admin and public APIs
- provide a separate admin website
- manage localized and uploaded media
- export a connected standalone package

---

# CHAPTER 5
# SOFTWARE DESIGN & MODELING

## 5.1 System Architecture

The project uses a modular architecture consisting of:

- Streamlit control app
- clone engine
- smart conversion engine
- Flask service layer
- React admin frontend
- SQLite persistence
- filesystem-backed clone/media/generated/export storage

## 5.2 Frontend Design

The project contains two main user-facing interfaces.

### 5.2.1 Streamlit Control Interface

This interface is responsible for:

- user authentication
- clone initiation
- project saving
- raw HTML management
- Smart Dynamic Conversion control
- connected export generation

### 5.2.2 Standalone React Admin Interface

This interface is responsible for:

- site-scoped login
- resource navigation based on `SiteSpec`
- record management
- publish/draft workflow
- media browsing, replacement, and upload
- diagnostics overview

### 5.2.3 GrapesJS Visual Editor Interface

This interface is served by Flask and supports visual editing of saved site HTML.

## 5.3 Modeling and Design View

For Milestone 3, the most important design diagrams are:

- Operational Diagram
- Component Diagram
- Deployment Diagram

These are prepared in [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio).

---

# CHAPTER 6
# ALGORITHM ANALYSIS

## 6.1 Clone Crawling Algorithm

The clone engine starts from the given root URL, normalizes it, crawls same-domain pages within configured limits, and records crawl order. It then rewrites links and assets into local paths.

## 6.2 Asset Rewriting Algorithm

The system rewrites:

- internal links
- CSS imports
- CSS `url(...)` references
- media source references
- preview paths

This is necessary to make the cloned output browsable locally and portable in exports.

## 6.3 Smart Conversion Algorithm

The conversion process:

1. parses cloned HTML
2. detects website type
3. extracts sections, navigation, forms, and media
4. infers resource models
5. generates seed records
6. computes confidence
7. builds `SiteSpec`
8. stores artifacts in DB and filesystem

## 6.4 Media Localization Algorithm

The media pipeline attempts to localize assets into `project_assets/media/site_<id>/`. If downloading fails, the system preserves external references while still indexing them.

---

# CHAPTER 7
# IMPLEMENTATION

## 7.1 Introduction

Milestone 3 implementation transforms StreamClone from a cloning proof of concept into a working application with separated runtime responsibilities, persistent storage, admin operations, and export packaging. The implementation now reflects actual working components rather than conceptual-only diagrams.

## 7.2 Major Implemented Modules

### 7.2.1 Streamlit Control App

Implemented in [app.py](../../app.py), this module handles:

- login and registration
- clone mode selection
- staged preview
- saving a project
- raw HTML editing
- Smart Dynamic Conversion
- connected export generation

### 7.2.2 Clone Engine

Implemented in [cloner_engine.py](../../cloner_engine.py), this module handles:

- page crawling
- sitemap-assisted discovery
- asset downloading and deduplication
- HTML/CSS/media rewriting
- bundle manifest creation
- clone ZIP export

### 7.2.3 Smart Conversion Engine

Implemented in [smart_conversion.py](../../smart_conversion.py), this module handles:

- site type detection
- media extraction
- section extraction
- model inference
- seed data generation
- confidence scoring
- `SiteSpec` creation

### 7.2.4 Flask Service Layer

Implemented in [dragdrop_flask.py](../../dragdrop_flask.py), this module handles:

- visual editor routes
- clone preview routes
- admin app static serving
- admin authentication APIs
- resource CRUD APIs
- media APIs
- public content APIs

### 7.2.5 Connected Export Packager

Implemented in [connected_export.py](../../connected_export.py), this module handles:

- package generation
- clone/admin/media/database bundling
- standalone backend generation
- ZIP archive creation

## 7.3 Component Diagram

The component diagram shows the software components and their dependencies in the Milestone 3 implementation.

Key components shown:

- Streamlit Control App
- Clone Engine
- Smart Conversion Engine
- Flask Service Layer
- React Admin Frontend
- Connected Export Packager
- SQLite Database
- Filesystem Storage

Suggested insertion:

- Insert `Component Diagram` page from [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)

Suggested caption:

`Figure 7.1: Component Diagram of StreamClone Milestone 3 Implementation`

## 7.4 Deployment Diagram

The deployment diagram shows how the implemented components are executed in the local runtime environment and how the standalone export runtime is organized.

Key deployment elements shown:

- browser
- Streamlit process on port `8501`
- Flask process on port `5001`
- `users.db`
- `project_assets/`
- optional exported package runtime on port `5010`

Suggested insertion:

- Insert `Deployment Diagram` page from [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)

Suggested caption:

`Figure 7.2: Deployment Diagram of StreamClone Milestone 3 Runtime`

## 7.5 Operational Diagram

The operational diagram explains the end-to-end working flow of the application.

Key steps shown:

- user action in Streamlit
- site cloning
- staged preview
- project saving
- Smart Dynamic Conversion
- admin/API serving
- connected export generation

Suggested insertion:

- Insert `Operational Diagram` page from [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)

Suggested caption:

`Figure 7.3: Operational Diagram of StreamClone Milestone 3 Workflow`

## 7.6 Current Implementation Status

At the end of Milestone 3, the project successfully demonstrates:

- clone package generation
- saved project persistence
- site editing
- `SiteSpec` generation
- record seeding
- media indexing
- admin panel routing and operations
- site-scoped content management
- connected export packaging

This makes the system demonstrable from the IDE as required by the M3 rubric.

---

# CHAPTER 8
# TESTING

## 8.1 Introduction

Testing for Milestone 3 focuses on validating the functional behavior of the implemented application. Since the project now includes multiple interacting modules, testing is divided into:

- black box testing
- white box testing

Black box testing validates externally visible behavior. White box testing validates logic-oriented internal behavior and code-level flows.

## 8.2 Black Box Test Cases

| Test ID | Module | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| BB-01 | Authentication | Register a new user with a unique username | User is created successfully and can log in | Pass |
| BB-02 | Authentication | Log in with invalid username/password | System rejects login and shows invalid credentials behavior | Pass |
| BB-03 | Clone Flow | Clone a valid public website URL | Staged preview, manifest, and clone bundle are generated | Pass |
| BB-04 | Save Project | Save a staged clone to the project database | Site is inserted into `cloned_sites` and clone package is persisted | Pass |
| BB-05 | Raw HTML Editor | Edit saved HTML and commit changes | Updated HTML is stored and rendered in preview | Pass |
| BB-06 | Smart Conversion | Generate database and admin panel for a saved site | `SiteSpec`, records, models, media, and artifacts are created | Pass |
| BB-07 | Admin Login | Open `/admin/site/<id>/login` and authenticate with valid account | Admin dashboard opens for that site | Pass |
| BB-08 | Resource CRUD | Create and update a resource record from the admin panel | Record is stored and shown in resource list | Pass |
| BB-09 | Media Library | Upload and replace media for a site | Media record updates and preview becomes available | Pass |
| BB-10 | Connected Export | Build connected export for a converted site | ZIP package is generated with clone, admin, DB, and media | Pass |
| BB-11 | Admin Build Missing | Access admin route without `admin/dist` present | System returns clear build-not-found behavior | Conditional / fallback handled |
| BB-12 | Unsupported Dynamic Site | Clone a highly JS-dependent target | Clone may not fully preserve behavior, but system still records the clone and conversion attempt | Limitation case |

## 8.3 White Box Test Cases

| Test ID | Function / Logic Area | Internal Validation Focus | Expected Outcome |
|---|---|---|---|
| WB-01 | `ensure_flask_running()` | Verify Flask auto-start behavior when port `5001` is not active | Flask process is started once and reused |
| WB-02 | `crawl_site_pages()` | Verify queue, visited-set, and depth/page-limit behavior | Internal crawl stops correctly at configured thresholds |
| WB-03 | `rewrite_css_text()` | Verify CSS `@import` and `url(...)` rewriting | Local asset references are rewritten correctly when downloadable |
| WB-04 | `build_conversion_blueprint()` | Verify blueprint contains site type, resources, media summary, diagnostics, and bindings | Blueprint is structurally complete |
| WB-05 | `rebuild_dynamic_site_data()` | Verify dynamic models and seed records are rebuilt from blueprint | Old rows are replaced and new rows reflect generated schema |
| WB-06 | `admin_publish_record()` | Verify only `draft` and `published` are accepted | Invalid status is rejected, valid state updates correctly |
| WB-07 | `build_connected_export()` | Verify export prerequisites and package folder creation | Export only succeeds when clone package, admin build, and generated artifacts exist |

## 8.4 Testing Summary

The current Milestone 3 implementation demonstrates that the system is functionally operational across its major flows. The most important validated behaviors are:

- cloning and bundle creation
- save and preview flows
- conversion pipeline execution
- admin login and CRUD
- media handling
- export packaging

The most important observed limitations are:

- dynamic JS-heavy sites may not clone perfectly
- some external assets may remain reference-only
- automatically inferred content structures may still need manual refinement

---

# CHAPTER 9
# DISCUSSION

## 9.1 Trade-offs and Design Decisions

The most important design decision in StreamClone is the move away from purely generative recreation and toward deterministic cloning plus structured conversion. This improves fidelity and traceability, but it also means the system must handle the complexity of real-world HTML, CSS, and resource relationships.

A second important design decision is the separation of concerns:

- Streamlit for orchestration
- Flask for serving and APIs
- React for admin operations

This makes the system more modular and easier to explain in Milestone 3 diagrams and demonstration.

## 9.2 Limitations

- heuristic inference may not perfectly identify all resource models
- not all external websites are equally clone-friendly
- the bridge model is practical, but not equivalent to a full re-architecture into a modern frontend framework

## 9.3 Why the Current State Still Matters

Despite its limitations, the current version is academically strong because it demonstrates:

- a working system
- clear module separation
- persistent storage
- diagrammable architecture
- a real upgrade from proof of concept to application

---

# CHAPTER 10
# CONCLUSION

## 10.1 Summary of Milestone 3

Milestone 3 represents the point at which StreamClone becomes a working application rather than only a cloning experiment. The project now supports the full flow from cloning to conversion to admin management and portable export packaging.

## 10.2 Key Outcomes

The key outcomes of Milestone 3 are:

- implemented clone engine
- saved project workflow
- `SiteSpec`-driven admin logic
- media pipeline
- admin CRUD and publish flow
- export package generation
- milestone-compliant component, deployment, and operational diagrams

## 10.3 Final Milestone 3 Statement

The current implementation satisfies the spirit of Milestone 3 by demonstrating a complete application from the IDE with actual operational flows, documented architecture, and working software components.

---

# CHAPTER 11
# FUTURE WORK

## 11.1 Improved Dynamic Website Support

Future versions can better support highly dynamic JavaScript-heavy sites through browser-driven rendering or hybrid capture approaches.

## 11.2 More Advanced Inference

The project can be improved by adding smarter field inference, deeper section classification, and richer content normalization.

## 11.3 More Robust Admin Features

Possible future enhancements include:

- role-based permissions
- better record validation
- richer media editing tools
- audit history

## 11.4 Deployment Beyond Local Runtime

The export package can eventually be extended into a more production-ready deployment model using containers, cloud databases, and automated hosting pipelines.

---

# CHAPTER 12
# ACHIEVEMENTS & VALIDATION

## 12.1 Major Achievements

The major Milestone 3 achievements are:

- successful upgrade from POC clone viewer to structured application
- implementation of separate admin website
- implementation of `SiteSpec`-driven resource navigation
- implementation of media localization and media library
- implementation of connected export packaging
- preparation of milestone-specific diagram set aligned to the rubric

## 12.2 Validation Through Architecture and Flow

The project now demonstrates:

- modularity
- reusability
- separation of concerns
- persistent runtime state
- extendable system structure

These are important because they directly improve the quality of the component and deployment diagrams required for Milestone 3.

## 12.3 Academic Value

The project shows a strong milestone progression:

- Milestone 2: proof of concept and strategic direction
- Milestone 3: implemented application with major flows and architecture
- Milestone 4: expected polishing, deployment strategy, and final documentation refinement

---

# CHAPTER 13
# APPENDICES

## Appendix A: Diagram Pack

Diagram source files:

- [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)
- [M3_DIAGRAMS_GUIDE.md](../diagrams/DIAGRAMS_GUIDE.md)

## Appendix B: Master Technical Documentation

- [AI_WEBSITE_FABRICATOR_MASTER_DOCUMENTATION.md](../MASTER_DOCUMENTATION.md)

## Appendix C: Generated and Runtime Artifacts

Relevant project folders:

- `project_assets/staged_clones/`
- `project_assets/clone_packages/`
- `project_assets/media/`
- `project_assets/generated_dynamic_apps/`
- `project_assets/connected_exports/`

## Appendix D: Suggested Figure Captions

- `Figure 7.1: Component Diagram of StreamClone Milestone 3 Implementation`
- `Figure 7.2: Deployment Diagram of StreamClone Milestone 3 Runtime`
- `Figure 7.3: Operational Diagram of StreamClone Milestone 3 Workflow`

## Appendix E: Key Source Files

- [app.py](../../app.py)
- [cloner_engine.py](../../cloner_engine.py)
- [smart_conversion.py](../../smart_conversion.py)
- [dragdrop_flask.py](../../dragdrop_flask.py)
- [connected_export.py](../../connected_export.py)

---

# CHAPTER 14
# REFERENCES

## 14.1 Literature and Technical References

1. Streamlit Documentation. Streamlit API Reference and Application Framework.
2. Flask Documentation. Flask Web Framework Documentation.
3. React Documentation. React User Interface Library Documentation.
4. Vite Documentation. Vite Frontend Tooling Documentation.
5. BeautifulSoup Documentation. HTML Parsing and DOM Processing Documentation.
6. Python `sqlite3` Documentation. SQLite Database Access in Python.
7. Requests Documentation. Python HTTP Client Library Documentation.
8. draw.io / diagrams.net. Diagram Authoring Environment.
9. Course handout: *Guidelines for 3rd and 4th Milestone* (extracted text: [source-material/m3_m4_guidelines_extracted.txt](source-material/m3_m4_guidelines_extracted.txt))
10. Course handout: *3rd Milestone Rubrics* (extracted text: [source-material/m3_rubrics_extracted.txt](source-material/m3_rubrics_extracted.txt))

## 14.2 Project Source References

1. [AI_WEBSITE_FABRICATOR_MASTER_DOCUMENTATION.md](../MASTER_DOCUMENTATION.md)
2. [M3_DIAGRAMS_GUIDE.md](../diagrams/DIAGRAMS_GUIDE.md)
3. [M3_DIAGRAMS.drawio](../diagrams/M3_DIAGRAMS.drawio)
