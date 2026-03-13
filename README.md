# 5051 Fauntleroy — 3-Week Look Ahead

A web app for the construction team to view and edit the project schedule online.

## Quick Start (Local)

```bash
cd schedule-app
pip install -r requirements.txt
py app.py
```

Open **http://localhost:5000** — the schedule loads in read-only mode.

To edit: click **Log In** and use one of the team accounts.

## Import Excel Data

```bash
py import_excel.py
```

## Editor Accounts

| Name | Email | Default Password |
|---|---|---|
| Edwin Tsay | edwin.tsay@pondviewseattle.com | team5051 |
| Emilio | emilio@greencanopynode.com | team5051 |
| Justin | justin@greencanopynode.com | team5051 |

## Deploy to Render

1. Push to GitHub
2. Create a new Web Service on Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add env vars: `SECRET_KEY`, `DATABASE_URL` (Render provides this with a PostgreSQL add-on)
