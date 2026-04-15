# Clone Media + Confidence Fix

## Root Cause

The old confidence score was low because it was mostly a site-type classification score, not a real clone-quality score. It did not look at:

- DOM preservation quality
- section extraction coverage
- style/layout preservation signals
- media recovery completeness
- link coverage
- interactive component detection

Media was missing from the admin panel because clone-time media ingestion never wrote clone assets into `media_assets`. Only manual uploads went there, so the admin media library had nothing real to display for cloned sites.

## End-to-End Fix

### Scraping / inference

- Added media extraction for:
  - `img`
  - lazy image attributes
  - `srcset`
  - `picture/source`
  - video/audio sources
  - favicons/icons
  - inline SVG
  - CSS background URLs from inline styles, style tags, and linked stylesheets
- Added section, navigation, theme-style, and page extraction
- Added media-aware seed records and section mappings

### Media storage

- Extended `media_assets` with metadata columns:
  - `asset_key`
  - `source_kind`
  - `media_type`
  - `mime_type`
  - `original_url`
  - `alt_text`
  - `width`
  - `height`
  - `hash`
  - `status`
  - `section_key`
  - `usage_json`
  - `metadata_json`
  - `local_path`
  - `updated_at`
- Added unique index on `(site_id, user_id, asset_key)`
- Localized downloaded media into `project_assets/media/site_<id>/`
- Preserved external fallback references when download was not possible

### Clone output / bridge

- Rewrote cloned HTML media URLs to localized media URLs where available
- Preserved original URLs in `data-fabricator-original-*` attributes
- Injected a clone bridge script so admin-managed `site_sections`, `navigation_items`, `site_pages`, and `theme_styles` can flow back into the cloned output

### Confidence scoring

- Replaced the old confidence logic with weighted scoring for:
  - DOM structure match
  - text extraction completeness
  - section detection accuracy
  - style match
  - layout match
  - media recovery completeness
  - link extraction completeness
  - interactive component detection
  - website type confidence
- Added transparent confidence breakdown and diagnostics into the generated blueprint and SiteSpec

### Admin panel

- Media API now returns clone-ingested media, not only manual uploads
- Added search/filter/preview/replace/delete support for media
- Added confidence breakdown + media summary to the admin overview
- Added media pickers in record editors for media fields

## Verified Backfill

- IQRA clone now has localized/indexed media and an improved confidence score
- Bahria clone now has localized/indexed media and an improved confidence score
