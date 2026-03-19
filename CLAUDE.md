# SupplementHub AI Label Automator

Product label generation system: PDF upload → AI-powered data extraction → multi-language translation → Adobe Illustrator automation.

## Tech Stack

- **Backend:** Python 3 / Flask, served via Waitress behind IIS (httpPlatformHandler)
- **Frontend:** Nuxt 3 (Vue 3, SSR) served via iisnode behind IIS
- **Label Automation:** Adobe Illustrator ExtendScript (.jsx), triggered via Windows Task Scheduler
- **AI:** OpenAI GPT-4o for PDF text extraction and structured label parsing
- **Hosting:** Windows Server / IIS

## Directory Structure

```
C:\inetpub\
├── python/                          # Flask backend
│   ├── app.py                       # Main Flask app (3 API routes)
│   ├── definitions.py               # Constants, prompts, config utilities
│   ├── utils.py                     # Archived utility functions
│   ├── requirements.txt             # Python dependencies
│   ├── web.config                   # IIS httpPlatform config (gitignored, contains secrets)
│   └── illustrator_script/
│       ├── script.jsx               # Main ExtendScript for Illustrator automation
│       ├── run_script.vbs           # VBScript wrapper to launch Illustrator
│       ├── libs/json2.js            # JSON parsing for ExtendScript
│       ├── labels/                  # Template .ai files (20+ label sizes)
│       ├── temp/                    # Working dir (config.json, barcode.eps, output/)
│       └── logs/                    # Illustrator script error logs
├── nuxt/                            # Nuxt 3 frontend (built/compiled output)
│   ├── server/index.mjs             # SSR entry point
│   ├── server/package.json          # Runtime Node dependencies
│   ├── public/                      # Static assets (CSS, fonts, images, _nuxt/)
│   ├── nitro.json                   # Build metadata (Nuxt 3.11.2, Nitro 2.9.6)
│   └── web.config                   # IIS iisnode config (gitignored, contains secrets)
├── test/                            # Test Flask app (hello world)
├── wwwroot/                         # IIS default web root
├── logs/                            # Application logs
└── temp/                            # Temporary files / IIS cache
```

## Running the Application

**Python backend** (IIS manages this automatically via web.config):
```bash
cd /c/inetpub/python
python -m waitress --port <PORT> app:app
```

**Nuxt frontend** (IIS manages this automatically via iisnode):
```bash
cd /c/inetpub/nuxt
node ./server/index.mjs
```

**Illustrator script** (triggered by Python backend via Task Scheduler):
```
schtasks /run /tn RunIllustratorScript
```

## API Endpoints

All endpoints require a `Token` header for authentication.

| Method | Path      | Description |
|--------|-----------|-------------|
| GET    | `/labels` | List available label templates (reads .ai files from labels/) |
| POST   | `/upload` | Upload PDF → converts to images → GPT-4o extracts structured label data as JSON |
| POST   | `/export` | Accepts label JSON → translates to FR/IT/ES/NL (+ EN if main language is English) → generates barcode → triggers Illustrator → returns .ai file |

### Required Export Fields
`label_size`, `barcode`, `product_name`, `key_features`, `additional_info`, `supplement_purpose`, `consumption_recommendation`, `ingredients_table`, `ingredients_table_footnotes`, `recommended_daily_dose`, `ingredients_list`, `warnings`, `quantity`, `net_weight`, `main_language` (optional, `"DE"` default or `"EN"`)

## Environment Variables

| Variable             | Where          | Purpose |
|----------------------|----------------|---------|
| `OPENAI_API_KEY`     | python/web.config | OpenAI API authentication |
| `FLASK_TOKEN`        | python/app.py  | API auth token (has hardcoded default) |
| `FLASK_DEBUG`        | python/web.config | Debug mode flag |
| `PYTHONPATH`         | python/web.config | Set to `C:\inetpub\python` |
| `HTTP_PLATFORM_PORT` | IIS (automatic) | Port assigned by IIS httpPlatform handler |
| `API_HOST`           | nuxt/web.config | Backend URL (default: `http://localhost:8080`) |

## Important Rules

- **Never modify files that are in .gitignore without explicit user permission.** This includes web.config files, logs, temp files, node_modules, and __pycache__.

## Key Conventions

- **web.config files are gitignored** — they contain secrets (API keys, tokens). Each IIS site has its own web.config.
- **Label templates** use prefix naming: BN- (BioNutra), NF- (NutraFlex) followed by dimensions.
- **Retry strategy:** 5 attempts for AI extraction, 5 attempts per language translation, 3 attempts for file save.
- **Parallel processing:** `ThreadPoolExecutor` for PDF pages, `concurrent.futures` for translations.
- **Font enforcement:** Legal minimums enforced per label area (7.1pt for labels ≥80cm², 5.0pt for <80cm²).
- **Languages:** German (source, default main language) or English (optional main language). Translations: French, Italian, Spanish, Dutch.
- **Illustrator layer structure:** Logo → Layout → Languages → Barcode+Recycling.

## Dependencies

**Python** (`python/requirements.txt`):
Flask, Flask-Cors, openai, pymupdf, pydantic, waitress, psutil, python-barcode, cairosvg

**Node** (`nuxt/server/package.json`):
Vue 3, Vue Router, GraphQL/Apollo, Pinia, VueUse, Axios, Tailwind Merge, Iconify
