import hmac
import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from functools import wraps

from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.utils import secure_filename

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

SERVICES = [
    {
        "icon": "🔧",
        "title": "Machine Troubleshooting & Repair",
        "desc": "On-site electrical and automation fault finding across production, "
                "filling, and packaging lines. Fast diagnosis, minimal downtime — "
                "whatever the brand of equipment.",
    },
    {
        "icon": "💻",
        "title": "PLC Programming & Upgrades",
        "desc": "Siemens and Allen-Bradley PLC programming, HMI and SCADA development, "
                "control system retrofits, and migration off obsolete hardware.",
    },
    {
        "icon": "📦",
        "title": "Spare Parts Supply",
        "desc": "Sourcing and supply of genuine and compatible spare parts for "
                "industrial lines — sensors, drives, servo motors, valves, control "
                "boards, and hard-to-find legacy items.",
    },
    {
        "icon": "🗓️",
        "title": "Preventive Maintenance Contracts",
        "desc": "Scheduled maintenance programs that maximize line availability, "
                "reduce unplanned stops, and extend the life of your equipment.",
    },
    {
        "icon": "🎓",
        "title": "Training & Consultancy",
        "desc": "Hands-on training for plant technicians, line and energy audits, "
                "spare parts strategy, and commissioning support for new equipment.",
    },
]

# Equipment manufacturers with direct hands-on experience.
OEM_BRANDS = ["Sidel", "Krones", "KHS", "SMI", "Sacmi", "Tetra Pak"]

CONTROL_PLATFORMS = [
    "Siemens S7 / TIA Portal",
    "Allen-Bradley / Rockwell",
    "Schneider Electric",
    "HMI & SCADA Systems",
    "VFDs & Servo Drives",
    "Profibus / Profinet / Ethernet-IP",
    "Instrumentation & Sensors",
    "Motor Control Centers (MCC)",
]

INDUSTRIES = [
    "Beverage & Bottling",
    "Food Processing",
    "Packaging & Palletizing",
    "Dairy & Juice",
    "Water Treatment",
    "General Manufacturing",
    "Utilities & Plant Services",
]

REQUEST_STATUSES = ["New", "Contacted", "Quoted", "Won", "Closed"]


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
            """CREATE TABLE IF NOT EXISTS brands (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   logo TEXT,
                   sort_order INTEGER NOT NULL DEFAULT 0,
                   show_on_site INTEGER NOT NULL DEFAULT 1
               )"""
        )
        # Added after the first version shipped; ignore if already present.
        cols = {r[1] for r in db.execute("PRAGMA table_info(service_requests)")}
        if "status" not in cols:
            db.execute(
                "ALTER TABLE service_requests ADD COLUMN status TEXT NOT NULL DEFAULT 'New'"
            )
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

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        supplied = request.form.get("password", "")
        if hmac.compare_digest(supplied, ADMIN_PASSWORD):
            session["admin"] = True
            session.permanent = False
            target = request.args.get("next", "")
            # Only follow internal paths, never an attacker-supplied URL.
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("admin_dashboard"))
        error = "Wrong password."
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.context_processor
def inject_globals():
    return {"using_default_password": ADMIN_PASSWORD == DEFAULT_PASSWORD}


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
        sent=request.args.get("sent") == "1",
    )


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
            request.form.get("phone", "").strip(),
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
    rows = get_db().execute(
        "SELECT * FROM service_requests ORDER BY id DESC"
    ).fetchall()
    return render_template("admin/requests.html", rows=rows, statuses=REQUEST_STATUSES)


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
@login_required
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

        values = (
            name,
            request.form.get("industry", "").strip(),
            request.form.get("location", "").strip(),
            request.form.get("contact_person", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("notes", "").strip(),
            1 if request.form.get("show_on_site") else 0,
        )
        if client_id is None:
            db.execute(
                """INSERT INTO clients
                       (name, industry, location, contact_person, phone, email,
                        notes, show_on_site, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values + (datetime.now().strftime("%Y-%m-%d %H:%M"),),
            )
            flash(f"Client “{name}” added.", "success")
        else:
            db.execute(
                """UPDATE clients SET name = ?, industry = ?, location = ?,
                       contact_person = ?, phone = ?, email = ?, notes = ?,
                       show_on_site = ?
                   WHERE id = ?""",
                values + (client_id,),
            )
            flash(f"Client “{name}” updated.", "success")
        db.commit()
        return redirect(url_for("admin_clients"))

    return render_template("admin/client_form.html", client=client)


@app.route("/admin/clients/<int:client_id>/delete", methods=["POST"])
@login_required
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
                client_names=client_names, services=SERVICES,
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
        client_names=client_names, services=SERVICES,
    )


@app.route("/admin/projects/<int:project_id>/delete", methods=["POST"])
@login_required
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
# Admin — equipment brands
# --------------------------------------------------------------------------

@app.route("/admin/brands")
@login_required
def admin_brands():
    rows = get_db().execute(
        "SELECT * FROM brands ORDER BY sort_order, id"
    ).fetchall()
    return render_template("admin/brands.html", rows=rows)


@app.route("/admin/brands/new", methods=["GET", "POST"])
@app.route("/admin/brands/<int:brand_id>/edit", methods=["GET", "POST"])
@login_required
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
@login_required
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
