# Demo Runbook

A step-by-step walkthrough for demonstrating the full **clone → convert → manage → reflect** flow on a local machine.

> Commands below assume an activated virtual environment and a working directory at the repository root.
> Windows users can substitute the launchers in [`../scripts/`](../scripts/).

## 1. What the demo proves

1. A site has been cloned, saved and converted.
2. The site-scoped admin panel is reachable and authenticated.
3. Content and media changes made in the admin surface through the public data endpoints.
4. The served clone uses the injected bridge and no-cache responses, so updates appear after a refresh.

## 2. Demo credentials

`prepare_demo.py` seeds a deterministic local demo user:

| Field | Value |
|---|---|
| Username | `jurydemo` |
| Password | `jurydemo123` |

```bash
python prepare_demo.py
```

This assigns the demo sites (for example `site 35` and `site 33`) to `jurydemo`.

> These credentials exist only in the local SQLite database created on your machine. They are not production credentials.

## 3. Start the services

Run each in its own terminal:

```bash
# Flask runtime, API and admin host
python dragdrop_flask.py

# Streamlit operator console
python -m streamlit run app.py
```

Or use the launchers:

```bash
./scripts/start_backend.sh      # Windows: scripts\start_backend.bat
./scripts/start_cloner.sh       # Windows: scripts\start_cloner.bat
```

## 4. Local URLs

| Surface | URL |
|---|---|
| Streamlit operator console | `http://127.0.0.1:8501` |
| Admin login (site 35) | `http://127.0.0.1:5001/admin/site/35/login` |
| Clone preview (site 35) | `http://127.0.0.1:5001/clone/35/` |
| Admin projects API | `http://127.0.0.1:5001/api/projects` |
| Public site sections | `http://127.0.0.1:5001/api/public/35/site_sections` |
| Public theme styles | `http://127.0.0.1:5001/api/public/35/theme_styles` |

## 5. Recommended demo sequence

1. Open `http://127.0.0.1:5001/admin/site/35/login`.
2. Log in as `jurydemo` / `jurydemo123`.
3. Open project `35`.
4. In the admin panel:
   - edit the title or summary of one `site_sections` record;
   - edit one theme/media value (`theme_styles.logo_url` or `theme_styles.favicon_url`) using a local `/media/35/...` URL.
5. Open the clone preview at `http://127.0.0.1:5001/clone/35/`.
6. Hard-refresh the page (`Ctrl+F5`).
7. Show that:
   - the public APIs contain the updated values;
   - the clone response includes the bridge script and no-cache headers.

## 6. Fast verification

Check that both services are up:

```bash
python -c "import requests; print(requests.get('http://127.0.0.1:5001/', timeout=5).status_code)"
python -c "import requests; print(requests.get('http://127.0.0.1:8501/', timeout=5).status_code)"
```

Check that an edit reached the public API:

```bash
python -c "import requests, json; print(json.dumps(requests.get('http://127.0.0.1:5001/api/public/35/site_sections', timeout=5).json(), indent=2)[:800])"
```

> An end-to-end `verify_demo_flow.py` helper was used during development but is not committed to this repository. The commands above cover the same checks.

## 7. Implementation notes

- Clone HTML is bridge-injected on served clone pages.
- Clone and media routes are served with no-cache headers.
- The media `PATCH` endpoint accepts multipart uploads without JSON parsing failures.
- Flask runs without the reloader by default. Set `AA_FLASK_DEBUG=1` only when needed.

## 8. Known limitations during a demo

- Use a fully cloned and converted site as the primary target; secondary targets should be re-cloned and reassigned to the demo user before presenting.
- Visible DOM updates depend on the selector quality captured during conversion. If a selector misses in one section, show the public API reflection plus another correctly mapped section.
