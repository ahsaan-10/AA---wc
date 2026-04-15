# AA / AI Website Fabricator - Jury Demo Runbook

This repository provides a local website cloning and editable CMS flow:

- Streamlit control app (`app.py`)
- Flask runtime/API/admin host (`dragdrop_flask.py`)
- Clone engine (`cloner_engine.py`)
- Smart conversion + bridge (`smart_conversion.py`)
- React site-scoped admin (`admin/src`, served from `admin/dist`)

## 1) Demo Goal (What to Show)

For the jury demo, prove this flow on localhost:

1. A site is already cloned/saved/converted (UITU first).
2. Local admin panel is accessible.
3. Admin-side content/media changes reflect through public data endpoints.
4. Clone preview uses bridge logic and no-cache responses so updates can show after refresh.

## 2) Known Demo Credentials

Use the deterministic local demo user:

- Username: `jurydemo`
- Password: `jurydemo123`

Prepare/refresh this user with:

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe prepare_demo.py
```

This currently assigns the UITU sites (`site 35`, `site 33`) to `jurydemo`.

## 3) Startup Commands

Run these in separate terminals from:

`c:\Users\lenovo\Downloads\aa`

### 3.1 Flask backend

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe dragdrop_flask.py
```

### 3.2 Streamlit control app

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe -m streamlit run app.py
```

## 4) Local URLs

- Streamlit: `http://127.0.0.1:8501`
- Admin login for UITU: `http://127.0.0.1:5001/admin/site/35/login`
- Clone preview for UITU: `http://127.0.0.1:5001/clone/35/`
- Admin projects API: `http://127.0.0.1:5001/api/projects`
- Public site sections API: `http://127.0.0.1:5001/api/public/35/site_sections`
- Public theme styles API: `http://127.0.0.1:5001/api/public/35/theme_styles`

## 5) Jury Demo Script (Recommended Sequence)

Use this exact order:

1. Open `http://127.0.0.1:5001/admin/site/35/login`.
2. Login with `jurydemo / jurydemo123`.
3. Open project `35` (UITU).
4. In admin:
   - Edit one `site_sections` record title/summary.
   - Edit one theme/media value (`theme_styles.logo_url` or `theme_styles.favicon_url`) using a local `/media/35/...` URL.
5. Open clone preview `http://127.0.0.1:5001/clone/35/`.
6. Hard refresh the page (`Ctrl+F5`).
7. Show that:
   - public APIs contain updated values
   - clone preview response includes bridge script and no-cache headers

## 6) Fast Verification Commands

### 6.1 One-step API flow verification (UITU)

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe verify_demo_flow.py --site-id 35
```

### 6.2 Flask health

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe -c "import requests; r=requests.get('http://127.0.0.1:5001/', timeout=5); print(r.status_code)"
```

### 6.3 Streamlit health

```powershell
c:\Users\lenovo\Downloads\aa\.venv\Scripts\python.exe -c "import requests; r=requests.get('http://127.0.0.1:8501/', timeout=5); print(r.status_code)"
```

## 7) Current Implementation Notes

- Clone HTML is bridge-injected on served clone pages.
- Clone and media routes are served with no-cache headers.
- Media PATCH endpoint supports multipart uploads without JSON parsing failures.
- Flask default run mode is stable (no reloader by default). Set `AA_FLASK_DEBUG=1` only if needed.

## 8) Known Limitations / Honest Fallback

- UITU (`site 35`) is the safest first demo target.
- Geo News and Al Jazeera should be treated as secondary targets unless they are freshly cloned and assigned to the demo user before presentation.
- Final visible DOM updates depend on selector quality extracted during conversion; if a selector misses in a specific section, show public API reflection and another successfully mapped section.
