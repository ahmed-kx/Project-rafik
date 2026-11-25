# Northvale University – Information & Announcement System

Small Flask + PostgreSQL web app (fictional university), deployed in two environments:

1. **Docker inside an Ubuntu VM** (VirtualBox) – app and database in separate containers
2. **Render** (PaaS) – web service + managed PostgreSQL

The **same code** runs in both. Only environment variables change.

## Files

| File | Role |
|---|---|
| `app.py` | Flask routes (public pages, login/logout, admin add/edit/delete) |
| `db.py` | Database connection, `run_query()` helper, automatic schema creation |
| `schema.sql` | Two tables (`departments`, `announcements`) + fictional sample data |
| `templates/` | Jinja2 pages: `base`, `index`, `departments`, `announcements`, `login`, `admin`, `edit` |
| `static/style.css` | The only stylesheet |
| `requirements.txt` | Flask, psycopg2-binary, gunicorn |
| `Dockerfile` | Image of the **web app only** |
| `docker-compose.yml` | Services `web` + `db`, network, volume |
| `.env.example` | Template for the secrets file `.env` |
| `.dockerignore`, `.gitignore` | Keep `.env` and junk out of the image / Git |
| `render.yaml` | Render Blueprint (web service + database) |

## Environment variables

| Variable | Meaning | Docker | Render |
|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | built by compose from `POSTGRES_*` (host = `db`) | from the Render database |
| `SECRET_KEY` | signs the session cookie | `.env` | generated / dashboard |
| `ADMIN_USERNAME` | admin login | `.env` | dashboard |
| `ADMIN_PASSWORD` | admin password | `.env` | dashboard |

On startup `db.py` connects (retrying for ~30 s), checks whether table `departments` exists, and runs `schema.sql` **only if it doesn't**. Data you add later is never overwritten.

---

## a) Run locally with Docker Compose

Requires Docker with the Compose plugin.

```bash
cp .env.example .env          # then edit .env: change ALL the passwords and SECRET_KEY
docker compose up --build -d
docker compose ps             # both services should be running (db "healthy")
docker compose logs web       # should say "Tables not found: running schema.sql ..." the first time
```

Open <http://localhost:5000>. Admin login: <http://localhost:5000/login> (credentials from `.env`).

Useful commands:

```bash
docker compose logs -f web      # follow the app logs
docker compose down             # stop + remove containers (data is KEPT in the volume)
docker compose down -v          # DANGER: also deletes the volume = deletes the data
```

Tip: keep `POSTGRES_PASSWORD` to letters and digits, because it is inserted in the `DATABASE_URL`.

---

## b) Ubuntu VM in VirtualBox

### b1) VirtualBox network mode: which one?

| Mode | Host → VM | VM → Internet | Verdict |
|---|---|---|---|
| **Bridged Adapter** | VM gets its own IP on your LAN (e.g. `192.168.1.50`). Host opens `http://192.168.1.50:5000` directly. | Yes | **Recommended** – simplest, and the brief wants access "through the VM's network address". |
| **NAT** (default) | VM is hidden. Host cannot reach it unless you add a **port-forwarding rule** (host `127.0.0.1:5000` → guest `5000`, and `2222` → `22` for SSH). Then you browse `http://127.0.0.1:5000`. | Yes | Works, but the app is reached through the *host's* address, not a VM address. |
| **Host-only** | VM gets an IP like `192.168.56.101`, reachable only from your PC. | **No** (can't `apt install` or pull images) | Good for isolation, but add a second NAT adapter for internet. |

**Choice:** Bridged. If bridging fails (university/public Wi-Fi often blocks it), use **two adapters: Adapter 1 = NAT** (internet) **+ Adapter 2 = Host-only** (host access via `192.168.56.x`).

VirtualBox → VM → Settings → Network → Adapter 1 → *Attached to: Bridged Adapter* → choose your real Wi-Fi/Ethernet card. Restart the VM after changing it.

### b2) Install Docker on Ubuntu (official repository)

Run inside the VM:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# let your user run docker without sudo (log out/in, or run: newgrp docker)
sudo usermod -aG docker $USER
newgrp docker

docker --version
docker compose version
docker run --rm hello-world     # quick test
```

If something differs for your Ubuntu version, check the official guide: <https://docs.docker.com/engine/install/ubuntu/>

### b3) Copy the project into the VM

**Option 1 – scp over SSH** (run the first command inside the VM, the second on the Windows host in PowerShell, from the folder that contains the project):

```bash
# inside the VM
sudo apt install -y openssh-server
ip -4 addr show            # find the VM IP (see b4)
```
```powershell
# on the host (do not copy your .env; you will create it in the VM)
scp -r "Project no balls" youruser@VM_IP:~/university-app
```

With NAT + port forwarding use `scp -P 2222 -r ... youruser@127.0.0.1:~/university-app`.

**Option 2 – Git:** push the project to a (private) GitHub repo and `git clone` it inside the VM.
**Option 3 – VirtualBox Shared Folder** (needs Guest Additions).

### b4) Run it and find the VM IP

```bash
cd ~/university-app
cp .env.example .env
nano .env                      # change passwords and SECRET_KEY
docker compose up --build -d
docker compose ps

hostname -I                    # the VM IP(s); or:  ip -4 addr show
```

If the Ubuntu firewall is active (`sudo ufw status`), allow the port: `sudo ufw allow 5000/tcp`.

### b5) Open the app from the physical host

First test the network (Part C): on the host, `ping VM_IP`.
Then open in the host browser: **`http://VM_IP:5000`** (Bridged / Host-only) or **`http://127.0.0.1:5000`** (NAT + port forwarding).

Check that PostgreSQL is **not** reachable from outside: from the host, `Test-NetConnection VM_IP -Port 5432` should fail, because the db container publishes no port.

---

## c) Prove data persistence

In the VM, inside the project folder:

```bash
# 1. In the browser: log in at /login, add an announcement titled "Persistence test".

# 2. Check it directly in PostgreSQL (variables are read from the container's own environment):
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, title, created_at FROM announcements ORDER BY id;"'

# 3. Destroy ONLY the db container (the volume stays):
docker compose rm -sf db
docker compose ps -a                # db is gone
docker volume ls                    # the volume <folder>_pgdata is still there

# 4. Recreate it:
docker compose up -d
docker compose ps                   # wait until db is "healthy"

# 5. Query again: "Persistence test" must still be there.
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, title FROM announcements ORDER BY id;"'

# 6. Optional: the app log shows the schema was skipped
docker compose logs web | grep -i "tables"
```

Refresh the site in the browser: the announcement is still displayed.
Useful for the report: `docker volume inspect <folder>_pgdata` (shows where Docker stores it on the VM disk). Do **not** run `docker compose down -v` during the proof: `-v` deletes the volume.

---

## d) Deploy on Render

**Before you start:** check Render's *current* pricing and free-plan limits yourself (<https://render.com/pricing> and the Render docs) and choose your plans knowing them. Write what you found, with the date, in your report.

First push this project to a GitHub (or GitLab) repository. **Do not push `.env`** (it is in `.gitignore`).

### Option 1 – Blueprint (uses `render.yaml`)

1. Render dashboard → **New +** → **Blueprint** → connect your repo.
2. Render reads `render.yaml` and proposes `university-web` + `university-db`.
3. It asks for the value of `ADMIN_PASSWORD` (marked `sync: false`). Enter one.
4. Check the plans shown, then **Apply**. Wait for the deploy to become *Live*.
5. Open the public URL `https://university-web-xxxx.onrender.com`.

### Option 2 – Manual setup

1. **Create the database:** New + → **PostgreSQL** → name `university-db`, choose a region and plan → Create.
   When it is ready, open it and copy the **Internal Database URL** (it works only for services in the *same region*).
2. **Create the web service:** New + → **Web Service** → connect the repo.
   - Language/Runtime: **Python 3**
   - Region: **same as the database**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 app:app`
3. **Environment variables:** in the web service → **Environment** tab → *Add Environment Variable*:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Internal Database URL copied above |
   | `SECRET_KEY` | a long random string (`python3 -c "import secrets; print(secrets.token_hex(32))"`) |
   | `ADMIN_USERNAME` | e.g. `admin` |
   | `ADMIN_PASSWORD` | a strong password |
   | `PYTHON_VERSION` | `3.12.3` (optional, to match the Dockerfile) |

4. **Create Web Service** and wait for *Live*. Open the URL. Check **Logs**: at the first start you should see `running schema.sql`.

### Verify on Render

Open the public URL, test every page, log in at `/login`, add/edit an announcement. To prove persistence, redeploy (Manual Deploy → *Deploy latest commit* or *Restart service*) and check the announcement is still there. You can also connect with `psql` using the database's **External Database URL** from the dashboard.

---

## e) Architecture summary

| Component | Environment 1 (VM + Docker) | Environment 2 (Render) |
|---|---|---|
| Web app | container `web` (image built from `Dockerfile`, gunicorn) | Render Web Service (Python runtime, gunicorn) |
| Database | container `db` (`postgres:16`) | Render PostgreSQL service |
| App ↔ DB link | user-defined bridge network `app-net`, host name `db`, port 5432 | Render internal URL (private network, same region) |
| Public port | **5000** (VM → `web`) | 443/HTTPS handled by Render; app listens on `$PORT` |
| DB port exposed? | **No** (5432 only inside `app-net`) | Not for the web, internal URL used (external URL exists but is optional) |
| Where data is stored | Docker named volume `pgdata` → `/var/lib/postgresql/data` (on the VM's virtual disk) | Render's managed database storage |
| Where secrets live | `.env` file in the VM (not in Git) | Render environment variables |
| Who manages the OS / patches | **Us** (Ubuntu, Docker, VM) | Render (we manage only app + config + data) |

| Container | Role | Image | Port inside | Published |
|---|---|---|---|---|
| `web` | Flask app served by gunicorn | built locally (`python:3.12-slim`) | 5000 | **5000:5000** |
| `db` | PostgreSQL | `postgres:16` | 5432 | none |

---

## Known simplifications (mention them in the report)

- The admin password is a plain environment variable (no hashing, single admin). Fine for a demo.
- No CSRF tokens on the admin forms. The session cookie is `SameSite=Lax` by default in modern browsers, but a real system should add CSRF protection.
- Docker environment uses plain HTTP; Render provides HTTPS automatically.
- gunicorn runs with 1 worker + 4 threads so that the "create tables" step runs once.

## Troubleshooting

| Problem | Likely fix |
|---|---|
| `KeyError: 'SECRET_KEY'` in the web logs | `.env` is missing or incomplete (compose also warns about unset variables) |
| Browser on the host times out | Wrong VM IP / network mode, or `sudo ufw allow 5000/tcp` |
| `password authentication failed` after changing `.env` | The volume still has the old password. Either revert the value or (loses data) `docker compose down -v` |
| Render: connection refused / timeout | Web service and database in different regions, or `DATABASE_URL` not set |
