# Putting the site online — free, step by step

Written for the PythonAnywhere account **`ahautomation`**.
Your live address will be **https://ahautomation.pythonanywhere.com**

## Short answer: use BOTH, they do different jobs

| | What it does | Can it run this site? |
|---|---|---|
| **PythonAnywhere** | Runs your Python code on a real server | **Yes — this is your host** |
| **GitHub** | Stores your code and delivers updates | No — it cannot run Python |

Your site has a **Request Service form** and an **admin panel**. When a client
fills the form in, Python has to receive it and save it. GitHub Pages only serves
plain files — it cannot run any Python at all, so on GitHub the form would look
fine but do nothing, and there would be no admin panel.

So: **PythonAnywhere hosts the site. GitHub stores the code and pushes updates to
it.** Both are free. GitHub is optional at the start, but it makes every future
update a one-line command instead of re-uploading files by hand.

---

## Part 1 — Put the code on GitHub

The local repository is already created and the first commit is already made.
You only need to create the GitHub side and push.

1. Create a free account at https://github.com
2. Click **+** (top right) → **New repository**.
   - **Repository name:** `services-site`
   - **Public** (see the note below — public is the easier and safe choice here)
   - **Do NOT tick** "Add a README file", "Add .gitignore", or "Choose a license".
     The repo must be completely empty or the push below will be rejected.
   - Click **Create repository**.
3. On your PC, open a terminal in `D:\12-REPORTS\services-site` and run these two
   commands, replacing `YOURUSER` with your GitHub username:

   ```
   git remote add origin https://github.com/YOURUSER/services-site.git
   git push -u origin main
   ```

   A browser window will open asking you to sign in to GitHub. Sign in and
   approve — Git remembers it after that, so you only do this once.

### Why public rather than private?

A **private** repo has to be authenticated again from PythonAnywhere, which
means generating a personal access token and pasting it into a server console —
fiddly, and easy to get wrong. A **public** repo clones on the server with no
login at all.

Public is safe here because **the repository contains no secrets**:

- Your admin password is not in the code — it is set on the server, in the WSGI
  file, which is never part of the repo.
- `requests.db` (clients, inquiries, projects) is excluded by `.gitignore`.
- `static/uploads/` (your job photos) is excluded.
- `.secret_key` (the session signing key) is excluded.

What is public is the website's own HTML, CSS, and Python — the same things any
visitor's browser already downloads. If you would still rather keep it private,
that is fine; just search PythonAnywhere's help for "clone a private GitHub
repo" and follow their token instructions.

---

## Part 2 — Host it on PythonAnywhere

### 1. Get the code onto the server
Open a **Bash console** (Consoles tab → **Bash**) and run **one** of these:

**If you used GitHub** (replace `YOURUSER` with your GitHub username):
```
git clone https://github.com/YOURUSER/services-site.git
```

**If you skipped GitHub:** go to the **Files** tab, upload a zip of the folder,
then in a Bash console run `unzip services-site.zip`.

Either way you should end up with the folder `/home/ahautomation/services-site`.
Check it with:
```
ls /home/ahautomation/services-site
```

### 2. Install Flask
Still in the Bash console:
```
pip install --user flask
```

### 3. Create the web app
- Go to the **Web** tab → **Add a new web app** → **Next**
- Choose **Manual configuration** (NOT "Flask" — manual gives you control)
- Pick a **Python 3.x** version → **Next**

### 4. Point it at your code
On the Web tab, find **Code** → **Source code** and set it to:
```
/home/ahautomation/services-site
```

### 5. Edit the WSGI file — and set your admin password
On the Web tab, click the link next to **WSGI configuration file**
(it will be `/var/www/ahautomation_pythonanywhere_com_wsgi.py`).

Delete everything in it and paste this, changing only the password:

```python
import os
import sys

sys.path.insert(0, "/home/ahautomation/services-site")

# Your admin password. Change it to something only you know.
os.environ["ADMIN_PASSWORD"] = "PutYourOwnPasswordHere"

from app import app as application
```

**This step is not optional.** Until you set `ADMIN_PASSWORD`, the admin panel
uses the default `changeme123`, and anyone who guesses it can read your client
list and delete your work. The admin pages show a warning banner until you
change it.

(There's a ready-made copy in `pythonanywhere_wsgi.py` in the project folder.)

### 6. Tell it where the CSS and photos live
Still on the Web tab, scroll to **Static files** and add:

| URL | Directory |
|---|---|
| `/static/` | `/home/ahautomation/services-site/static/` |

Without this the site loads but looks unstyled and project photos won't appear.

### 7. Reload
Click the big green **Reload** button, then visit:

**https://ahautomation.pythonanywhere.com**

Your admin panel is at:

**https://ahautomation.pythonanywhere.com/admin**

---

## First things to do once you're live

1. **Log into `/admin`** and confirm the yellow "default password" warning is
   gone. If it's still there, the `ADMIN_PASSWORD` line didn't take — check the
   WSGI file and hit Reload again.
2. **Add your real phone number.** Edit `templates/index.html` and replace
   `+000 000 000 000`.
3. **Add a few jobs under "Work Done"** with photos. This is what convinces a
   plant manager to call you.
4. **Add your clients** — tick "show on site" only for the ones happy to be named.

---

## Updating the site later

Change a file on your PC, then:

```
git add .
git commit -m "what changed"
git push
```

Then in a PythonAnywhere Bash console:
```
cd /home/ahautomation/services-site && git pull
```
And click **Reload** on the Web tab.

---

## Things to know about the free plan

- **Your address is `ahautomation.pythonanywhere.com`.** A custom domain like
  `ahautomation.com` needs a paid plan (~$5/month). Fine to start free and
  upgrade once you have paying clients.
- **Every 3 months** PythonAnywhere emails you to click a button confirming the
  site is still in use. Ignore it and the site goes offline — don't let that
  email get buried.
- **Email notifications won't work on the free plan.** Free accounts can't send
  mail out. That's exactly why requests are stored in the admin panel instead —
  bookmark `https://ahautomation.pythonanywhere.com/admin` on your phone and
  check it daily.
- **Your data lives on the server, not in git.** `requests.db` (clients,
  requests, projects) and `static/uploads/` (photos) are deliberately excluded
  from git, so `git pull` will never overwrite them. Download `requests.db`
  from the Files tab now and then as a backup.
- **Free accounts have a CPU-seconds quota.** A brochure site like this uses
  very little, so you will not hit it under normal traffic.
