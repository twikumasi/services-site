# AH Automation Services — Website

Professional services website for industrial electrical & automation work across
factories and production lines. Flask + SQLite.

## Admin panel — `/admin`

Password-protected. Default password is `changeme123` — override it by setting
the `ADMIN_PASSWORD` environment variable (see [DEPLOY.md](DEPLOY.md)). A warning
banner shows in the admin until you do.

| Page | What you can do |
|---|---|
| **Dashboard** | Counts at a glance, latest requests, quick-add buttons |
| **Requests** | Read client inquiries, set status (New → Contacted → Quoted → Won → Closed), delete |
| **Clients** | Add / edit / delete clients, with private notes; tick to show on the website |
| **Work Done** | Add jobs with a photo, client, machine, date, and description; tick to show on the website |
| **Brands** | Manage the equipment brands shown on the site; optionally upload a logo image |

Photos upload to `static/uploads/` (JPG, PNG, GIF, WEBP — max 8 MB each).
Anything with "show on site" unticked stays private to the admin.

## Run locally

```
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deploy

Live host: **PythonAnywhere**, account `ahautomation` →
https://ahautomation.pythonanywhere.com

**See [DEPLOY.md](DEPLOY.md)** — the full step-by-step guide, already filled in
with the real username and paths. `pythonanywhere_wsgi.py` holds the exact WSGI
config to paste on the server.

## Customizing

- **Phone number:** `templates/index.html` — search for `+000`.
- **Business name:** "AH Automation Services" in `templates/index.html`.
- **Equipment brands:** managed from the admin panel (`/admin/brands`) — no code
  editing needed.
- **Control platforms and industries:** plain Python lists near the top of
  `app.py` (`CONTROL_PLATFORMS`, `INDUSTRIES`).
- **Logo:** `static/logo.svg`.

## Data that must not be committed

`requests.db` (requests, clients, projects), `static/uploads/` (photos), and
`.secret_key` are all in `.gitignore` on purpose. They live only on the server,
so `git pull` can never overwrite real client data. Back up `requests.db` from
the PythonAnywhere Files tab from time to time.
