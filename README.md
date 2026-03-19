# SupplementHub AI Label Automator

Product label generation system: PDF upload → AI-powered data extraction → multi-language translation → Adobe Illustrator automation.

## Git Workflow

### Branches

- **`master`** — Historical snapshot of the old VM state. **Do not push to this branch.**
- **`latest-changes`** — The active development branch. All new work merges here.

### Working on a Task

1. Create a new branch from `latest-changes`:
   ```
   git checkout latest-changes
   git pull
   git checkout -b story/TICKET-ID
   ```
2. Make your changes and commit.
3. Push your branch and open a **Pull Request** targeting `latest-changes`.
4. After review, merge the PR into `latest-changes`.

## Application Workflow

### Export Flow (User Perspective)

1. Open the frontend in the browser (served by IIS via the Nuxt site).
2. **Step 1 — Upload**: Upload a product PDF. The backend sends it to GPT-4o, which extracts structured label data in German.
3. **Step 2 — Review & Edit**: Review the extracted data, select a label template, choose the main language (Deutsch or English), and edit fields if needed.
4. **Step 3 — Export**: Click export. The backend:
   - Translates label fields to French, Italian, Spanish, and Dutch (+ English if selected as main language).
   - Generates a barcode (EPS) from the provided barcode number.
   - Writes a `config.json` with all label data to `python/illustrator_script/temp/`.
   - Triggers Adobe Illustrator via Windows Task Scheduler (`RunIllustratorScript`).
   - Illustrator runs `script.jsx`, which reads the config, populates the `.ai` template, and saves `output.ai` to `python/illustrator_script/temp/output/`.
   - The backend detects the output file and streams it back to the browser as a download.

### API Endpoints

All endpoints are served by the Python/Flask backend behind IIS. Requests require a `Token` header.

| Method | Path      | Description |
|--------|-----------|-------------|
| GET    | `/labels` | List available label templates |
| POST   | `/upload` | Upload PDF → GPT-4o extracts structured label data as JSON |
| POST   | `/export` | Accepts label JSON → translates → generates barcode → triggers Illustrator → returns `.ai` file |

## Restarting After Code Changes

Whenever you modify files in `python/` or `nuxt/`, you must restart IIS for the changes to take effect:

```
iisreset
```

This restarts both the Nuxt frontend and the Python backend. IIS may also recycle app pools automatically on file changes, but `iisreset` guarantees a clean restart.
