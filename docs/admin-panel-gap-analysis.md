# Separate Admin Panel Gap Analysis

## Repository Inspection

### What already existed

- `app.py`
  - Streamlit cloner dashboard
  - user auth
  - clone/save flow
  - code editor view for saved HTML
  - launch point for drag and drop builder
- `dragdrop_flask.py`
  - separate Flask interface for GrapesJS drag and drop editing
  - asset upload support
  - saved-site editor routes
- `smart_conversion.py`
  - rules-based website type detection
  - inferred content models
  - seed record generation
  - scaffold file generation
- `users.db`
  - users and cloned sites persisted in SQLite

### What was missing

- standalone admin website
- SiteSpec-first API contract for external admin UI
- admin auth endpoint for a separate frontend
- project/spec endpoints
- publish status controls
- media library endpoints
- explicit public read-only content API for cloned sites

### What must stay untouched

- Streamlit cloner workflow in `app.py`
- code editor flow in `app.py`
- drag and drop builder in `dragdrop_flask.py`
- cloned HTML preservation
- non-React cloned frontend editing model

## Gap Analysis

### Gap 1: Admin UI location was wrong

The earlier implementation exposed admin CRUD inside the cloner dashboard. That violated the product boundary in the Milestone 3 plan, which requires a separate admin application.

### Gap 2: SiteSpec was not the live contract

Blueprint JSON existed, but the external interface did not yet consume a stable `SiteSpec` contract through project/spec APIs.

### Gap 3: APIs were incomplete for a real CMS

There were dynamic collection APIs, but not the project list, SiteSpec, publish, media, and admin-auth routes needed by a separate CMS application.

### Gap 4: No standalone routing or auth flow

There was no separate login, dashboard, projects page, or resource-based routing outside the cloner.

## Change Plan Applied

1. Keep the cloner and builder intact.
2. Store generated `SiteSpec` separately from the cloner UI.
3. Keep fixed record tables instead of per-site SQL tables.
4. Add Flask admin APIs for:
   - auth
   - projects
   - SiteSpec
   - resource CRUD
   - publish
   - media
   - public read-only data
5. Create a standalone `/admin` React + TypeScript + Vite application.
6. Remove the embedded admin experience from the Streamlit conversion flow.
7. Verify the original cloner/editor routes still work.

## Result

The project now has:

- one cloner website for cloning and structural editing
- one separate admin website for content management
- SiteSpec-backed resource navigation
- publishable records
- public read-only endpoints for frontend consumption
