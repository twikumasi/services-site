import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, g, jsonify, make_response, redirect,
                   render_template, request, send_from_directory, session,
                   url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from translations import DEFAULT_LANG, LANGUAGES, translate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "requests.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB per photo

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# The admin password. Override it on the server by setting ADMIN_PASSWORD.
DEFAULT_PASSWORD = "changeme123"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", DEFAULT_PASSWORD)


def _load_secret_key():
    """Persist a random session key so logins survive a server restart."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_path = os.path.join(BASE_DIR, ".secret_key")
    if os.path.exists(key_path):
        with open(key_path) as fh:
            return fh.read().strip()
    key = secrets.token_hex(32)
    with open(key_path, "w") as fh:
        fh.write(key)
    return key


app.secret_key = _load_secret_key()

# Each service is a pair of translation keys; the template resolves them.
SERVICES = [
    {"icon": "🔧", "key": "svc_repair"},
    {"icon": "💻", "key": "svc_plc"},
    {"icon": "📦", "key": "svc_parts"},
    {"icon": "🗓️", "key": "svc_pm"},
    {"icon": "🎓", "key": "svc_training"},
]
# The admin panel is English-only, so service names are stored and shown in
# English there regardless of the visitor language on the public site.
SERVICE_TITLES = [translate(s["key"], "en") for s in SERVICES]

# Equipment manufacturers with direct hands-on experience.
OEM_BRANDS = ["Sidel", "Krones", "KHS", "SMI", "Sacmi", "Tetra Pak"]

CONTROL_PLATFORMS = [
    "plat_siemens", "plat_ab", "plat_schneider", "plat_hmi",
    "plat_drives", "plat_networks", "plat_instr", "plat_mcc",
]

INDUSTRIES = [
    "ind_beverage", "ind_food", "ind_packaging", "ind_dairy",
    "ind_water", "ind_manufacturing", "ind_utilities",
]

REQUEST_STATUSES = ["New", "Contacted", "Quoted", "Won", "Closed"]

# Who can do what. Staff handle day-to-day work; only an admin can change the
# business itself (users, contract wording, contact details, branding) or delete
# records permanently.
ROLES = {
    "admin": "Administrator — full access",
    "staff": "Staff — requests, jobs and clients only",
}
ADMIN_ONLY_HINT = "That area is for administrators only."

CONTRACT_STATUSES = ["Draft", "Sent", "Signed", "Cancelled"]

# Dial codes offered on the request form. The three home markets come first —
# Sudan is the default — and everything after that is alphabetical so a visitor
# can find their country without guessing how the list is grouped.
COUNTRY_CODES = [
    ("+249", "🇸🇩 Sudan"),
    ("+233", "🇬🇭 Ghana"),
    ("+20", "🇪🇬 Egypt"),
    ("+213", "🇩🇿 Algeria"),
    ("+973", "🇧🇭 Bahrain"),
    ("+226", "🇧🇫 Burkina Faso"),
    ("+237", "🇨🇲 Cameroon"),
    ("+235", "🇹🇩 Chad"),
    ("+86", "🇨🇳 China"),
    ("+225", "🇨🇮 Côte d'Ivoire"),
    ("+291", "🇪🇷 Eritrea"),
    ("+251", "🇪🇹 Ethiopia"),
    ("+33", "🇫🇷 France"),
    ("+49", "🇩🇪 Germany"),
    ("+91", "🇮🇳 India"),
    ("+964", "🇮🇶 Iraq"),
    ("+39", "🇮🇹 Italy"),
    ("+962", "🇯🇴 Jordan"),
    ("+254", "🇰🇪 Kenya"),
    ("+965", "🇰🇼 Kuwait"),
    ("+961", "🇱🇧 Lebanon"),
    ("+218", "🇱🇾 Libya"),
    ("+212", "🇲🇦 Morocco"),
    ("+31", "🇳🇱 Netherlands"),
    ("+234", "🇳🇬 Nigeria"),
    ("+968", "🇴🇲 Oman"),
    ("+92", "🇵🇰 Pakistan"),
    ("+974", "🇶🇦 Qatar"),
    ("+966", "🇸🇦 Saudi Arabia"),
    ("+221", "🇸🇳 Senegal"),
    ("+27", "🇿🇦 South Africa"),
    ("+211", "🇸🇸 South Sudan"),
    ("+34", "🇪🇸 Spain"),
    ("+963", "🇸🇾 Syria"),
    ("+255", "🇹🇿 Tanzania"),
    ("+228", "🇹🇬 Togo"),
    ("+216", "🇹🇳 Tunisia"),
    ("+90", "🇹🇷 Turkey"),
    ("+971", "🇦🇪 UAE"),
    ("+256", "🇺🇬 Uganda"),
    ("+44", "🇬🇧 United Kingdom"),
    ("+1", "🇺🇸 USA / Canada"),
    ("+967", "🇾🇪 Yemen"),
]
VALID_DIAL_CODES = {code for code, _ in COUNTRY_CODES}

# Editable from /admin/settings. Keys are fixed; values are whatever Ahmad sets.
DEFAULT_SETTINGS = {
    "business_name": "AH Automation Services",
    "tagline": "Industrial Electrical & Automation",
    "phone": "+000 000 000 000",
    "whatsapp": "",
    "email": "ahmad.hamdi@twellium.com",
    "availability": "Available for on-site work & remote support",
    "linkedin_url": "",
    "facebook_url": "",
}


# --------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS service_requests (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   created_at TEXT NOT NULL,
                   name TEXT NOT NULL,
                   company TEXT,
                   phone TEXT NOT NULL,
                   email TEXT,
                   machine TEXT,
                   service TEXT,
                   message TEXT
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS clients (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   created_at TEXT NOT NULL,
                   name TEXT NOT NULL,
                   industry TEXT,
                   location TEXT,
                   contact_person TEXT,
                   phone TEXT,
                   email TEXT,
                   notes TEXT,
                   show_on_site INTEGER NOT NULL DEFAULT 1
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS projects (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   created_at TEXT NOT NULL,
                   title TEXT NOT NULL,
                   client TEXT,
                   machine TEXT,
                   service TEXT,
                   date_done TEXT,
                   description TEXT,
                   image TEXT,
                   show_on_site INTEGER NOT NULL DEFAULT 1
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS settings (
                   key TEXT PRIMARY KEY,
                   value TEXT NOT NULL
               )"""
        )
        db.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            list(DEFAULT_SETTINGS.items()),
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS brands (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   logo TEXT,
                   sort_order INTEGER NOT NULL DEFAULT 0,
                   show_on_site INTEGER NOT NULL DEFAULT 1
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS users (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                   password_hash TEXT NOT NULL,
                   full_name TEXT,
                   role TEXT NOT NULL DEFAULT 'staff',
                   active INTEGER NOT NULL DEFAULT 1,
                   created_at TEXT NOT NULL
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS contract_templates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT NOT NULL,
                   service TEXT,
                   body TEXT NOT NULL,
                   created_at TEXT NOT NULL
               )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS contracts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   client_id INTEGER NOT NULL,
                   template_id INTEGER,
                   title TEXT NOT NULL,
                   service TEXT,
                   body TEXT NOT NULL,
                   status TEXT NOT NULL DEFAULT 'Draft',
                   reference TEXT,
                   created_at TEXT NOT NULL,
                   created_by TEXT,
                   FOREIGN KEY (client_id) REFERENCES clients(id)
               )"""
        )

        # Columns added after the first version shipped; ignore if present.
        def add_column(table, column, spec):
            cols = {r[1] for r in db.execute(f"PRAGMA table_info({table})")}
            if column not in cols:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")

        add_column("service_requests", "status", "TEXT NOT NULL DEFAULT 'New'")
        add_column("service_requests", "assigned_to", "INTEGER")
        add_column("clients", "logo", "TEXT")

        # The first admin comes from ADMIN_PASSWORD so there is always a way in.
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            db.execute(
                """INSERT INTO users (username, password_hash, full_name, role,
                                      active, created_at)
                   VALUES (?, ?, ?, 'admin', 1, ?)""",
                ("admin", generate_password_hash(ADMIN_PASSWORD), "Owner",
                 datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
        elif ADMIN_PASSWORD != DEFAULT_PASSWORD:
            # The site may have been started once before ADMIN_PASSWORD was set.
            # If the built-in admin is still on the factory password, adopt the
            # new one — so "set it in the WSGI file and reload" works as
            # documented. Once a real password is in place this never fires
            # again, and passwords changed in the Team page are left alone.
            row = db.execute(
                "SELECT id, password_hash FROM users WHERE username = 'admin'"
            ).fetchone()
            if row and check_password_hash(row[1], DEFAULT_PASSWORD):
                db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                           (generate_password_hash(ADMIN_PASSWORD), row[0]))
        # Seed the brand list once so the site isn't empty on first run.
        if db.execute("SELECT COUNT(*) FROM brands").fetchone()[0] == 0:
            db.executemany(
                "INSERT INTO brands (name, sort_order, show_on_site) VALUES (?, ?, 1)",
                [(name, i) for i, name in enumerate(OEM_BRANDS)],
            )


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

def current_user():
    """The logged-in user row, or None. Cached per request."""
    if "_user" not in g:
        uid = session.get("user_id")
        g._user = None
        if uid:
            g._user = get_db().execute(
                "SELECT * FROM users WHERE id = ? AND active = 1", (uid,)
            ).fetchone()
    return g._user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            session.pop("user_id", None)
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Everything a staff account must not reach."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return redirect(url_for("admin_login", next=request.path))
        if user["role"] != "admin":
            flash(ADMIN_ONLY_HINT, "error")
            return redirect(url_for("admin_dashboard"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM users WHERE username = ? AND active = 1", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session["user_id"] = row["id"]
            session.permanent = False
            target = request.args.get("next", "")
            # Only follow internal paths, never an attacker-supplied URL.
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("admin_dashboard"))
        error = "Wrong username or password."
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("user_id", None)
    return redirect(url_for("admin_login"))


def get_raw_settings():
    """Exactly what is stored, with no fallbacks — what the edit form must show."""
    values = dict(DEFAULT_SETTINGS)
    for row in get_db().execute("SELECT key, value FROM settings"):
        if row["key"] in DEFAULT_SETTINGS:
            values[row["key"]] = row["value"]
    return values


def get_settings():
    """Display values for the public site, with sensible fallbacks applied."""
    values = get_raw_settings()
    # An empty WhatsApp field means "same number as the phone". This is resolved
    # at display time, never saved, so changing the phone keeps them in sync.
    if not values["whatsapp"].strip():
        values["whatsapp"] = values["phone"]
    return values


def tel_link(number):
    """Strip spaces/dashes so tel: and wa.me links work."""
    cleaned = "".join(ch for ch in number if ch.isdigit() or ch == "+")
    return cleaned


def current_lang():
    """Language for this request: ?lang= wins, then the saved cookie."""
    requested = request.args.get("lang") or request.cookies.get("lang")
    return requested if requested in LANGUAGES else DEFAULT_LANG


@app.route("/lang/<code>")
def set_language(code):
    """Switch language and return to the page the visitor came from."""
    if code not in LANGUAGES:
        code = DEFAULT_LANG
    target = request.args.get("next", "")
    if not (target.startswith("/") and not target.startswith("//")):
        target = url_for("index")
    response = make_response(redirect(target))
    # A year, so the choice sticks between visits.
    response.set_cookie("lang", code, max_age=31536000, samesite="Lax")
    return response


@app.context_processor
def inject_globals():
    lang = current_lang()
    user = current_user() if session.get("user_id") else None
    return {
        "user": user,
        "is_admin": bool(user and user["role"] == "admin"),
        "using_default_password": ADMIN_PASSWORD == DEFAULT_PASSWORD,
        "settings": get_settings(),
        "tel_link": tel_link,
        "lang": lang,
        "lang_dir": LANGUAGES[lang]["dir"],
        "other_lang": "ar" if lang == "en" else "en",
        "other_lang_label": LANGUAGES[lang]["switch_to"],
        "t": lambda key: translate(key, lang),
    }


# --------------------------------------------------------------------------
# Uploads
# --------------------------------------------------------------------------

def save_upload(file_storage):
    """Save an uploaded photo and return its stored filename, or None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None
    # Random name avoids collisions and stops a crafted filename escaping the dir.
    stem = secure_filename(os.path.splitext(file_storage.filename)[0])[:40] or "photo"
    filename = f"{stem}-{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_storage.save(os.path.join(UPLOAD_DIR, filename))
    return filename


def delete_upload(filename):
    if not filename:
        return
    path = os.path.join(UPLOAD_DIR, filename)
    # Guard against a stored value pointing outside the uploads folder.
    if os.path.commonpath([os.path.abspath(path), UPLOAD_DIR]) != UPLOAD_DIR:
        return
    if os.path.exists(path):
        os.remove(path)


# --------------------------------------------------------------------------
# Public site
# --------------------------------------------------------------------------

@app.route("/")
def index():
    db = get_db()
    projects = db.execute(
        "SELECT * FROM projects WHERE show_on_site = 1 ORDER BY id DESC"
    ).fetchall()
    clients = db.execute(
        "SELECT * FROM clients WHERE show_on_site = 1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    brands = db.execute(
        "SELECT * FROM brands WHERE show_on_site = 1 ORDER BY sort_order, id"
    ).fetchall()
    return render_template(
        "index.html",
        services=SERVICES,
        brands=brands,
        platforms=CONTROL_PLATFORMS,
        industries=INDUSTRIES,
        projects=projects,
        clients=clients,
        country_codes=COUNTRY_CODES,
        sent=request.args.get("sent") == "1",
    )


@app.route("/work/<int:project_id>")
def project_detail(project_id):
    """A page per job, so each one has its own link to share. LinkedIn reads the
    Open Graph tags here to build the preview card."""
    project = get_db().execute(
        "SELECT * FROM projects WHERE id = ? AND show_on_site = 1", (project_id,)
    ).fetchone()
    if project is None:
        return render_template("not_found.html"), 404
    return render_template("project.html", p=project)


@app.route("/manifest.webmanifest")
def manifest():
    """Installable-app metadata. Served from Flask so the app name follows
    whatever business name is set in the admin."""
    s = get_settings()
    data = {
        "name": s["business_name"],
        "short_name": s["business_name"].split()[0] if s["business_name"] else "Services",
        "description": s["tagline"],
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0d1b2a",
        "theme_color": "#0d1b2a",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192",
             "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512",
             "type": "image/png", "purpose": "any"},
            {"src": "/static/icons/icon-maskable-192.png", "sizes": "192x192",
             "type": "image/png", "purpose": "maskable"},
            {"src": "/static/icons/icon-maskable-512.png", "sizes": "512x512",
             "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "Admin Panel", "url": "/admin"},
            {"name": "Request Service", "url": "/#contact"},
        ],
    }
    response = jsonify(data)
    response.headers["Content-Type"] = "application/manifest+json"
    return response


@app.route("/sw.js")
def service_worker():
    """Served from the site root so the worker's scope covers every page —
    a worker under /static/ could only control /static/."""
    response = send_from_directory(os.path.join(BASE_DIR, "static"), "sw.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response


def combine_phone(dial_code, local_number):
    """Join the chosen country code with the number the visitor typed.

    Visitors often type the code themselves or start with a national trunk
    prefix ('0111...'), so strip both rather than storing '+20 +20' or '+200111'.
    """
    local = "".join(ch for ch in local_number if ch.isdigit() or ch == "+").strip()
    if dial_code not in VALID_DIAL_CODES:
        dial_code = COUNTRY_CODES[0][0]
    if local.startswith("+"):
        # Already fully international — trust it and ignore the dropdown.
        return local
    digits = dial_code.lstrip("+")
    if local.startswith(digits):
        local = local[len(digits):]
    local = local.lstrip("0")
    return f"{dial_code}{local}" if local else ""


@app.route("/request", methods=["POST"])
def submit_request():
    db = get_db()
    db.execute(
        """INSERT INTO service_requests
               (created_at, name, company, phone, email, machine, service, message, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'New')""",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            request.form.get("name", "").strip(),
            request.form.get("company", "").strip(),
            combine_phone(request.form.get("country_code", ""),
                          request.form.get("phone", "")),
            request.form.get("email", "").strip(),
            request.form.get("machine", "").strip(),
            request.form.get("service", "").strip(),
            request.form.get("message", "").strip(),
        ),
    )
    db.commit()
    return redirect(url_for("index", sent=1) + "#contact")


# --------------------------------------------------------------------------
# Admin — dashboard
# --------------------------------------------------------------------------

@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    stats = {
        "new_requests": db.execute(
            "SELECT COUNT(*) FROM service_requests WHERE status = 'New'"
        ).fetchone()[0],
        "requests": db.execute("SELECT COUNT(*) FROM service_requests").fetchone()[0],
        "clients": db.execute("SELECT COUNT(*) FROM clients").fetchone()[0],
        "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
    }
    recent = db.execute(
        "SELECT * FROM service_requests ORDER BY id DESC LIMIT 5"
    ).fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


# --------------------------------------------------------------------------
# Admin — service requests
# --------------------------------------------------------------------------

@app.route("/admin/requests")
@login_required
def admin_requests():
    db = get_db()
    mine = request.args.get("mine") == "1"
    sql = ("SELECT r.*, u.username AS assignee, u.full_name AS assignee_name "
           "FROM service_requests r LEFT JOIN users u ON u.id = r.assigned_to ")
    params = ()
    if mine:
        sql += "WHERE r.assigned_to = ? "
        params = (session.get("user_id"),)
    rows = db.execute(sql + "ORDER BY r.id DESC", params).fetchall()
    team = db.execute(
        "SELECT id, username, full_name FROM users WHERE active = 1 "
        "ORDER BY username COLLATE NOCASE"
    ).fetchall()
    return render_template("admin/requests.html", rows=rows,
                           statuses=REQUEST_STATUSES, team=team, mine=mine)


@app.route("/admin/requests/<int:req_id>/assign", methods=["POST"])
@login_required
def assign_request(req_id):
    raw = request.form.get("assigned_to", "")
    db = get_db()
    assignee = None
    if raw:
        row = db.execute("SELECT id FROM users WHERE id = ? AND active = 1",
                         (raw,)).fetchone()
        assignee = row["id"] if row else None
    db.execute("UPDATE service_requests SET assigned_to = ? WHERE id = ?",
               (assignee, req_id))
    db.commit()
    return redirect(request.referrer or url_for("admin_requests"))


@app.route("/admin/requests/<int:req_id>/status", methods=["POST"])
@login_required
def update_request_status(req_id):
    status = request.form.get("status", "New")
    if status not in REQUEST_STATUSES:
        status = "New"
    db = get_db()
    db.execute("UPDATE service_requests SET status = ? WHERE id = ?", (status, req_id))
    db.commit()
    return redirect(url_for("admin_requests"))


@app.route("/admin/requests/<int:req_id>/delete", methods=["POST"])
@admin_required
def delete_request(req_id):
    db = get_db()
    db.execute("DELETE FROM service_requests WHERE id = ?", (req_id,))
    db.commit()
    flash("Request deleted.", "success")
    return redirect(url_for("admin_requests"))


# --------------------------------------------------------------------------
# Admin — clients
# --------------------------------------------------------------------------

@app.route("/admin/clients")
@login_required
def admin_clients():
    rows = get_db().execute(
        "SELECT * FROM clients ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return render_template("admin/clients.html", rows=rows)


@app.route("/admin/clients/new", methods=["GET", "POST"])
@app.route("/admin/clients/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def client_form(client_id=None):
    db = get_db()
    client = None
    if client_id is not None:
        client = db.execute(
            "SELECT * FROM clients WHERE id = ?", (client_id,)
        ).fetchone()
        if client is None:
            flash("That client no longer exists.", "error")
            return redirect(url_for("admin_clients"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Client name is required.", "error")
            return render_template("admin/client_form.html", client=client)

        logo = client["logo"] if client else None
        uploaded = save_upload(request.files.get("logo"))
        if uploaded:
            if logo:
                delete_upload(logo)
            logo = uploaded
        elif request.files.get("logo") and request.files["logo"].filename:
            flash("Logo not saved — use a PNG, JPG, GIF, or WEBP file.", "error")
        if request.form.get("remove_logo") and logo:
            delete_upload(logo)
            logo = None

        values = (
            name,
            request.form.get("industry", "").strip(),
            request.form.get("location", "").strip(),
            request.form.get("contact_person", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("notes", "").strip(),
            logo,
            1 if request.form.get("show_on_site") else 0,
        )
        if client_id is None:
            db.execute(
                """INSERT INTO clients
                       (name, industry, location, contact_person, phone, email,
                        notes, logo, show_on_site, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values + (datetime.now().strftime("%Y-%m-%d %H:%M"),),
            )
            flash(f"Client “{name}” added.", "success")
        else:
            db.execute(
                """UPDATE clients SET name = ?, industry = ?, location = ?,
                       contact_person = ?, phone = ?, email = ?, notes = ?,
                       logo = ?, show_on_site = ?
                   WHERE id = ?""",
                values + (client_id,),
            )
            flash(f"Client “{name}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_clients"))

    return render_template("admin/client_form.html", client=client)


@app.route("/admin/clients/<int:client_id>")
@login_required
def client_profile(client_id):
    """Everything about one client, including their contracts."""
    db = get_db()
    client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if client is None:
        flash("That client no longer exists.", "error")
        return redirect(url_for("admin_clients"))
    contracts = db.execute(
        "SELECT * FROM contracts WHERE client_id = ? ORDER BY id DESC", (client_id,)
    ).fetchall()
    templates = db.execute(
        "SELECT id, title, service FROM contract_templates ORDER BY title COLLATE NOCASE"
    ).fetchall()
    projects = db.execute(
        "SELECT * FROM projects WHERE client = ? ORDER BY id DESC", (client["name"],)
    ).fetchall()
    return render_template("admin/client_profile.html", client=client,
                           contracts=contracts, templates=templates,
                           projects=projects, statuses=CONTRACT_STATUSES)


@app.route("/admin/clients/<int:client_id>/delete", methods=["POST"])
@admin_required
def delete_client(client_id):
    db = get_db()
    db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    db.commit()
    flash("Client deleted.", "success")
    return redirect(url_for("admin_clients"))


# --------------------------------------------------------------------------
# Admin — projects / work done
# --------------------------------------------------------------------------

@app.route("/admin/projects")
@login_required
def admin_projects():
    rows = get_db().execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
    return render_template("admin/projects.html", rows=rows)


@app.route("/admin/projects/new", methods=["GET", "POST"])
@app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
@login_required
def project_form(project_id=None):
    db = get_db()
    project = None
    if project_id is not None:
        project = db.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            flash("That project no longer exists.", "error")
            return redirect(url_for("admin_projects"))

    client_names = [
        r["name"] for r in db.execute(
            "SELECT name FROM clients ORDER BY name COLLATE NOCASE"
        )
    ]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Project title is required.", "error")
            return render_template(
                "admin/project_form.html", project=project,
                client_names=client_names, services=SERVICE_TITLES,
            )

        image = project["image"] if project else None
        uploaded = save_upload(request.files.get("image"))
        if uploaded:
            if image:
                delete_upload(image)
            image = uploaded
        elif request.files.get("image") and request.files["image"].filename:
            flash("Photo not saved — use a JPG, PNG, GIF, or WEBP file.", "error")
        if request.form.get("remove_image") and image:
            delete_upload(image)
            image = None

        values = (
            title,
            request.form.get("client", "").strip(),
            request.form.get("machine", "").strip(),
            request.form.get("service", "").strip(),
            request.form.get("date_done", "").strip(),
            request.form.get("description", "").strip(),
            image,
            1 if request.form.get("show_on_site") else 0,
        )
        if project_id is None:
            db.execute(
                """INSERT INTO projects
                       (title, client, machine, service, date_done, description,
                        image, show_on_site, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values + (datetime.now().strftime("%Y-%m-%d %H:%M"),),
            )
            flash(f"Project “{title}” added.", "success")
        else:
            db.execute(
                """UPDATE projects SET title = ?, client = ?, machine = ?,
                       service = ?, date_done = ?, description = ?, image = ?,
                       show_on_site = ?
                   WHERE id = ?""",
                values + (project_id,),
            )
            flash(f"Project “{title}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_projects"))

    return render_template(
        "admin/project_form.html", project=project,
        client_names=client_names, services=SERVICE_TITLES,
    )


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@admin_required
def delete_project(project_id):
    db = get_db()
    row = db.execute(
        "SELECT image FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if row:
        delete_upload(row["image"])
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    flash("Project deleted.", "success")
    return redirect(url_for("admin_projects"))


# --------------------------------------------------------------------------
# Admin — contract templates and issued contracts
# --------------------------------------------------------------------------

def fill_placeholders(text, client, extra=None):
    """Substitute {{client_name}}-style placeholders with real values."""
    s = get_settings()
    values = {
        "client_name": client["name"] if client else "",
        "client_company": client["name"] if client else "",
        "client_contact": (client["contact_person"] or "") if client else "",
        "client_location": (client["location"] or "") if client else "",
        "client_phone": (client["phone"] or "") if client else "",
        "client_email": (client["email"] or "") if client else "",
        "company_name": s["business_name"],
        "company_phone": s["phone"],
        "company_email": s["email"],
        "date": datetime.now().strftime("%d %B %Y"),
    }
    values.update(extra or {})
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


@app.route("/admin/contracts")
@login_required
def admin_contracts():
    db = get_db()
    templates = db.execute(
        "SELECT * FROM contract_templates ORDER BY title COLLATE NOCASE"
    ).fetchall()
    issued = db.execute(
        "SELECT c.*, cl.name AS client_name FROM contracts c "
        "JOIN clients cl ON cl.id = c.client_id ORDER BY c.id DESC LIMIT 50"
    ).fetchall()
    return render_template("admin/contracts.html", templates=templates,
                           issued=issued, statuses=CONTRACT_STATUSES)


@app.route("/admin/contracts/templates/new", methods=["GET", "POST"])
@app.route("/admin/contracts/templates/<int:template_id>/edit", methods=["GET", "POST"])
@admin_required
def contract_template_form(template_id=None):
    db = get_db()
    template = None
    if template_id is not None:
        template = db.execute(
            "SELECT * FROM contract_templates WHERE id = ?", (template_id,)
        ).fetchone()
        if template is None:
            flash("That contract template no longer exists.", "error")
            return redirect(url_for("admin_contracts"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        service = request.form.get("service", "").strip()
        if not title or not body:
            flash("A template needs both a title and the terms text.", "error")
            return render_template("admin/contract_template_form.html",
                                   template=template, services=SERVICE_TITLES)
        if template_id is None:
            db.execute(
                "INSERT INTO contract_templates (title, service, body, created_at) "
                "VALUES (?, ?, ?, ?)",
                (title, service, body, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            flash(f"Template “{title}” created.", "success")
        else:
            db.execute(
                "UPDATE contract_templates SET title = ?, service = ?, body = ? "
                "WHERE id = ?", (title, service, body, template_id),
            )
            flash(f"Template “{title}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_contracts"))

    return render_template("admin/contract_template_form.html",
                           template=template, services=SERVICE_TITLES)


@app.route("/admin/contracts/templates/<int:template_id>/delete", methods=["POST"])
@admin_required
def delete_contract_template(template_id):
    db = get_db()
    db.execute("DELETE FROM contract_templates WHERE id = ?", (template_id,))
    db.commit()
    flash("Template deleted. Contracts already issued are unaffected.", "success")
    return redirect(url_for("admin_contracts"))


@app.route("/admin/clients/<int:client_id>/contracts/new", methods=["POST"])
@login_required
def issue_contract(client_id):
    """Create a contract for a client from a template, snapshotting the wording
    so later edits to the template never alter an issued contract."""
    db = get_db()
    client = db.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if client is None:
        flash("That client no longer exists.", "error")
        return redirect(url_for("admin_clients"))

    template = db.execute(
        "SELECT * FROM contract_templates WHERE id = ?",
        (request.form.get("template_id", ""),)
    ).fetchone()
    if template is None:
        flash("Pick a contract template first.", "error")
        return redirect(url_for("client_profile", client_id=client_id))

    now = datetime.now()
    reference = f"{now.strftime('%Y%m')}-{client_id:03d}-{now.strftime('%H%M%S')}"
    body = fill_placeholders(template["body"], client, {"reference": reference})
    db.execute(
        """INSERT INTO contracts (client_id, template_id, title, service, body,
                                  status, reference, created_at, created_by)
           VALUES (?, ?, ?, ?, ?, 'Draft', ?, ?, ?)""",
        (client_id, template["id"], template["title"], template["service"], body,
         reference, now.strftime("%Y-%m-%d %H:%M"),
         current_user()["username"]),
    )
    db.commit()
    flash(f"Contract “{template['title']}” created for {client['name']}.", "success")
    return redirect(url_for("client_profile", client_id=client_id))


@app.route("/admin/contracts/<int:contract_id>")
@login_required
def view_contract(contract_id):
    db = get_db()
    contract = db.execute(
        "SELECT c.*, cl.name AS client_name, cl.contact_person, cl.location, "
        "cl.phone AS client_phone, cl.email AS client_email "
        "FROM contracts c JOIN clients cl ON cl.id = c.client_id WHERE c.id = ?",
        (contract_id,)
    ).fetchone()
    if contract is None:
        flash("That contract no longer exists.", "error")
        return redirect(url_for("admin_contracts"))
    return render_template("admin/contract_view.html", c=contract,
                           statuses=CONTRACT_STATUSES)


@app.route("/admin/contracts/<int:contract_id>/status", methods=["POST"])
@login_required
def update_contract_status(contract_id):
    status = request.form.get("status", "Draft")
    if status not in CONTRACT_STATUSES:
        status = "Draft"
    db = get_db()
    db.execute("UPDATE contracts SET status = ? WHERE id = ?", (status, contract_id))
    db.commit()
    flash(f"Contract marked as {status}.", "success")
    return redirect(request.referrer or url_for("view_contract", contract_id=contract_id))


@app.route("/admin/contracts/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
def edit_contract(contract_id):
    db = get_db()
    contract = db.execute(
        "SELECT * FROM contracts WHERE id = ?", (contract_id,)
    ).fetchone()
    if contract is None:
        flash("That contract no longer exists.", "error")
        return redirect(url_for("admin_contracts"))
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        title = request.form.get("title", "").strip() or contract["title"]
        db.execute("UPDATE contracts SET body = ?, title = ? WHERE id = ?",
                   (body, title, contract_id))
        db.commit()
        flash("Contract updated.", "success")
        return redirect(url_for("view_contract", contract_id=contract_id))
    return render_template("admin/contract_edit.html", c=contract)


@app.route("/admin/contracts/<int:contract_id>/delete", methods=["POST"])
@admin_required
def delete_contract(contract_id):
    db = get_db()
    row = db.execute("SELECT client_id FROM contracts WHERE id = ?",
                     (contract_id,)).fetchone()
    db.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
    db.commit()
    flash("Contract deleted.", "success")
    if row:
        return redirect(url_for("client_profile", client_id=row["client_id"]))
    return redirect(url_for("admin_contracts"))


# --------------------------------------------------------------------------
# Admin — team members
# --------------------------------------------------------------------------

@app.route("/admin/users")
@admin_required
def admin_users():
    rows = get_db().execute(
        "SELECT * FROM users ORDER BY role, username COLLATE NOCASE"
    ).fetchall()
    return render_template("admin/users.html", rows=rows, roles=ROLES)


@app.route("/admin/users/new", methods=["GET", "POST"])
@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def user_form(user_id=None):
    db = get_db()
    member = None
    if user_id is not None:
        member = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if member is None:
            flash("That user no longer exists.", "error")
            return redirect(url_for("admin_users"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "staff")
        if role not in ROLES:
            role = "staff"
        full_name = request.form.get("full_name", "").strip()
        active = 1 if request.form.get("active") else 0

        error = None
        if not username:
            error = "Username is required."
        elif member is None and len(password) < 8:
            error = "Give the new user a password of at least 8 characters."
        elif password and len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            clash = db.execute(
                "SELECT id FROM users WHERE username = ? AND id IS NOT ?",
                (username, user_id),
            ).fetchone()
            if clash:
                error = f"The username “{username}” is already taken."

        # Never let the last active admin be demoted or switched off — that
        # would lock everyone out of the admin area for good.
        if not error and member is not None and member["role"] == "admin":
            other_admins = db.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1 "
                "AND id != ?", (user_id,)
            ).fetchone()[0]
            if other_admins == 0 and (role != "admin" or not active):
                error = ("This is the only administrator left. Add another admin "
                         "before changing this one.")

        if error:
            flash(error, "error")
            return render_template("admin/user_form.html", member=member, roles=ROLES)

        if member is None:
            db.execute(
                """INSERT INTO users (username, password_hash, full_name, role,
                                      active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, generate_password_hash(password), full_name, role,
                 active, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            flash(f"User “{username}” created.", "success")
        else:
            db.execute(
                "UPDATE users SET username = ?, full_name = ?, role = ?, active = ? "
                "WHERE id = ?", (username, full_name, role, active, user_id),
            )
            if password:
                db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                           (generate_password_hash(password), user_id))
            flash(f"User “{username}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_users"))

    return render_template("admin/user_form.html", member=member, roles=ROLES)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    db = get_db()
    if user_id == session.get("user_id"):
        flash("You cannot delete the account you are signed in with.", "error")
        return redirect(url_for("admin_users"))
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row and row["role"] == "admin":
        others = db.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin' AND active = 1 AND id != ?",
            (user_id,)
        ).fetchone()[0]
        if others == 0:
            flash("That is the only administrator — create another one first.", "error")
            return redirect(url_for("admin_users"))
    db.execute("UPDATE service_requests SET assigned_to = NULL WHERE assigned_to = ?",
               (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/password", methods=["GET", "POST"])
@login_required
def change_password():
    """Any signed-in user can change their own password."""
    if request.method == "POST":
        user = current_user()
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        if not check_password_hash(user["password_hash"], current):
            flash("Your current password is not correct.", "error")
        elif len(new) < 8:
            flash("The new password must be at least 8 characters.", "error")
        elif new != request.form.get("confirm_password", ""):
            flash("The two new passwords do not match.", "error")
        else:
            db = get_db()
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                       (generate_password_hash(new), user["id"]))
            db.commit()
            flash("Your password has been changed.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin/password.html")


# --------------------------------------------------------------------------
# Admin — site settings (contact details)
# --------------------------------------------------------------------------

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    db = get_db()
    if request.method == "POST":
        for key in DEFAULT_SETTINGS:
            value = request.form.get(key, "").strip()
            db.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        db.commit()
        flash("Contact details updated — they are live on the website now.", "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin/settings.html", values=get_raw_settings())


# --------------------------------------------------------------------------
# Admin — equipment brands
# --------------------------------------------------------------------------

@app.route("/admin/brands")
@admin_required
def admin_brands():
    rows = get_db().execute(
        "SELECT * FROM brands ORDER BY sort_order, id"
    ).fetchall()
    return render_template("admin/brands.html", rows=rows)


@app.route("/admin/brands/new", methods=["GET", "POST"])
@app.route("/admin/brands/<int:brand_id>/edit", methods=["GET", "POST"])
@admin_required
def brand_form(brand_id=None):
    db = get_db()
    brand = None
    if brand_id is not None:
        brand = db.execute(
            "SELECT * FROM brands WHERE id = ?", (brand_id,)
        ).fetchone()
        if brand is None:
            flash("That brand no longer exists.", "error")
            return redirect(url_for("admin_brands"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Brand name is required.", "error")
            return render_template("admin/brand_form.html", brand=brand)

        logo = brand["logo"] if brand else None
        uploaded = save_upload(request.files.get("logo"))
        if uploaded:
            if logo:
                delete_upload(logo)
            logo = uploaded
        elif request.files.get("logo") and request.files["logo"].filename:
            flash("Logo not saved — use a PNG, JPG, GIF, or WEBP file.", "error")
        if request.form.get("remove_logo") and logo:
            delete_upload(logo)
            logo = None

        try:
            sort_order = int(request.form.get("sort_order") or 0)
        except ValueError:
            sort_order = 0

        values = (name, logo, sort_order,
                  1 if request.form.get("show_on_site") else 0)
        if brand_id is None:
            db.execute(
                "INSERT INTO brands (name, logo, sort_order, show_on_site) "
                "VALUES (?, ?, ?, ?)", values
            )
            flash(f"Brand “{name}” added.", "success")
        else:
            db.execute(
                "UPDATE brands SET name = ?, logo = ?, sort_order = ?, "
                "show_on_site = ? WHERE id = ?", values + (brand_id,)
            )
            flash(f"Brand “{name}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_brands"))

    return render_template("admin/brand_form.html", brand=brand)


@app.route("/admin/brands/<int:brand_id>/delete", methods=["POST"])
@admin_required
def delete_brand(brand_id):
    db = get_db()
    row = db.execute("SELECT logo FROM brands WHERE id = ?", (brand_id,)).fetchone()
    if row:
        delete_upload(row["logo"])
    db.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
    db.commit()
    flash("Brand deleted.", "success")
    return redirect(url_for("admin_brands"))


@app.errorhandler(413)
def too_large(error):
    flash("That photo is too big — maximum size is 8 MB.", "error")
    return redirect(url_for("admin_projects"))


init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
