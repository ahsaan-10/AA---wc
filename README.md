# Website Fabricator Prototype

**A Python prototype exploring website capture, structure inference, and editable content workflows.**

## What the code explores

- Reference-page capture and localized asset bundles.
- Inference of site structure, models, pages, sections, navigation, and theme settings.
- Streamlit orchestration of capture and conversion.
- Flask routes for previews, admin/public APIs, and content operations.
- Connected export packaging.

The reusable output is inferred structure and starter data. It does not reconstruct a source website's private backend or guarantee a complete CMS for every website.

## Public repository status

The Python operator, capture engine, conversion module, Flask runtime, and export module are present. The public tree reviewed on 5 October 2026 does **not** include the `admin/` frontend referenced by the runtime, or the `users.db` file expected by the existing demo setup. The bundled `project_data.db` is a different file. The prior site-specific jury walkthrough therefore cannot be assumed to work from a fresh clone.

Treat this as an engineering prototype until frontend assets and a repeatable database initialization flow are supplied and verified.

## Explore the implementation

```text
app.py              Streamlit operator interface
cloner_engine.py    Capture, assets, link rewriting, bundle packaging
smart_conversion.py Structure inference and generated-site bindings
dragdrop_flask.py   Runtime, API, preview, and admin-serving routes
connected_export.py Export packaging
prepare_demo.py     Existing local demo preparation script
requirements.txt    Python dependencies
```

See [the architecture documentation](AI_WEBSITE_FABRICATOR_MASTER_DOCUMENTATION.md) for the broader implementation explanation. Local walkthroughs in existing reports depend on their original demo environment.

## Local setup starting point

```bash
git clone https://github.com/ahsaan-10/AA---wc.git
cd AA---wc
python -m venv .venv
```

Activate the environment and install dependencies:

```bash
python -m pip install -r requirements.txt
```

After resolving the frontend and database prerequisites, the intended entry points are:

```bash
python dragdrop_flask.py
python -m streamlit run app.py
```

Run these in separate terminals. Expected local ports are 5001 for Flask and 8501 for Streamlit. These are setup entry points, not a claim that the current public checkout has passed a fresh-install test.

## Presentation focus

Explain capture → inferred structure → editable content → export. Use a website you own or have permission to use, and show which updates are visible in the API and which are successfully mapped into a preview.
