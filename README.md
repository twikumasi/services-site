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
| **Contact** | Edit the business name, tagline, phone, WhatsApp, email, and availability line — changes go live immediately |

Inquiry phone numbers are stored in full international form (`+20…`). The public
form pairs a country dropdown with the number and normalises what visitors type,
so every number in the admin is dialable as-is. Add or reorder countries in
`COUNTRY_CODES` near the top of `app.py`.

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

## Arabic / English

A 🌐 button in the header switches the public site between English and Arabic.
The choice is stored in a `lang` cookie for a year, so returning visitors keep
their language. `?lang=ar` overrides it for a single request.

Arabic pages render right-to-left (`dir="rtl"`). Phone numbers, dial codes, and
email addresses are forced back to left-to-right, because an RTL phone number is
unreadable.

**What is and isn't translated:**

- **Translated:** every fixed word on the public site — navigation, headings,
  service names and descriptions, industries, control platforms, form labels,
  buttons, and the non-affiliation notice. All of it lives in `translations.py`.
- **Not translated:** anything typed into the admin — job titles and
  descriptions, client names, brand names, and your contact details. These show
  exactly as entered. Brand names (Sidel, Krones, KHS…) are proper nouns and
  deliberately stay in Latin script in both languages.
- **The admin panel is English only.** It is your own working tool, not a
  customer-facing page.

To add or reword a string, edit the `("English", "العربية")` pair in
`translations.py`. To add a third language, add it to `LANGUAGES` and extend each
tuple.

**If you write job descriptions in Arabic**, they will appear in Arabic for
English visitors too, since job text is never translated. For a bilingual
portfolio, write both languages into the description field.

## LinkedIn

Two separate things:

**Linking to your page** — admin → **Contact** → LinkedIn Page. Paste the full
address and a LinkedIn button appears in the contact section. Leave it blank to
hide it.

**Posting a job to LinkedIn** — admin → **Work Done** → the blue **in Share**
button on any published job. It opens LinkedIn's share window with that job's
page attached; you add your own comment and press Post. Each job has its own
public page at `/work/<id>` carrying Open Graph tags, so LinkedIn shows the
photo, title, and description as a preview card. The same link previews properly
in WhatsApp and Facebook.

The button only appears on jobs ticked "show on site" — an unpublished job has no
public page to share, and `/work/<id>` returns 404 for it.

### Why there is no fully automatic posting

Auto-publishing to LinkedIn from the server would need LinkedIn's Marketing API:
a registered app, company-page verification, an OAuth flow, and access tokens
that expire and must be refreshed. On top of that, **PythonAnywhere free accounts
cannot make arbitrary outbound HTTPS requests** — traffic goes through a proxy
that only allows whitelisted sites, and `api.linkedin.com` is not on it. So a
server-side LinkedIn integration cannot work on the current plan at all.

The share button achieves the same outcome in two clicks with no tokens to
maintain, and it lets you write a different comment for each post, which
performs better on LinkedIn anyway.

## Installable Android / iPhone app

The site is a **Progressive Web App**: on a phone, the browser offers "Add to
Home screen" and it then launches full-screen with its own icon, no browser bar.
No app store, no build step, no cost.

Pieces involved:

- `/manifest.webmanifest` — generated by Flask so the app name follows whatever
  business name is set in the admin.
- `/sw.js` — service worker, served from the site root so its scope covers the
  whole site. Caches the public shell; **never** caches `/admin`.
  - Pages, CSS, and JS use **network-first**, so a deployed change shows up
    immediately. Serving these from cache would freeze the site's appearance for
    anyone who had already loaded the old files.
  - Images use cache-first — icons and uploaded photos have unique filenames, so
    a cached copy can never be stale.
  - Bump `CACHE` in `static/sw.js` if you ever need to force every visitor onto a
    clean cache.
- `static/offline.html` — shown when the phone has no signal.
- `static/icons/` — 192px and 512px icons plus maskable variants, generated
  from `logo.svg`.

Requires HTTPS, which PythonAnywhere provides. `localhost` also counts as secure
for testing.

## Customizing

- **Phone, WhatsApp, email, business name:** admin panel → **Contact**. No code
  editing.
- **Equipment brands:** admin panel → **Brands**.
- **Control platforms and industries:** plain Python lists near the top of
  `app.py` (`CONTROL_PLATFORMS`, `INDUSTRIES`).
- **Logo:** `static/logo.svg`. If you change it, regenerate the app icons so the
  home-screen icon matches.

## Data that must not be committed

`requests.db` (requests, clients, projects), `static/uploads/` (photos), and
`.secret_key` are all in `.gitignore` on purpose. They live only on the server,
so `git pull` can never overwrite real client data. Back up `requests.db` from
the PythonAnywhere Files tab from time to time.
