# Hospify Deployment Guide

**Architecture:**
| Service | Where | Cost |
|---------|-------|------|
| Frontend (HTML/CSS/JS) | ProFreeHost (public_html/) | Free |
| Backend (Flask API + MySQL) | PythonAnywhere | Free |

---

## Part 1: Backend → PythonAnywhere

### 1.1 Create Account
1. Go to https://www.pythonanywhere.com
2. Sign up for **Free Beginner** account (no credit card)
3. Your API URL will be: `https://YOURUSERNAME.pythonanywhere.com`

### 1.2 Create MySQL Database
1. Dashboard → **Databases** → **Create a MySQL database**
2. Note the database name, username, and password
3. Click **Open phpMyAdmin**
4. Import `database/hospify.sql` (File → Choose File → Go)

### 1.3 Upload Backend Files
1. Dashboard → **Files** tab
2. Navigate to `/home/YOURUSERNAME/`
3. Create a directory: `hospify`
4. Upload ALL files from the `backend/` folder into `/home/YOURUSERNAME/hospify/`
5. Create an `uploads` directory inside it

### 1.4 Set Up Virtual Environment
1. Dashboard → **Consoles** → **Bash**
2. Run:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 hospify-env
   cd ~/hospify
   pip install -r requirements.txt
   ```

### 1.5 Configure Web App
1. Dashboard → **Web** → **Add a new web app**
2. Click **Manual configuration** → **Python 3.10** → Next
3. In the **Code** section:
   - **Source code**: `/home/YOURUSERNAME/hospify`
   - **Working directory**: `/home/YOURUSERNAME/hospify`
4. Click the **WSGI configuration file** link to edit it
5. Replace everything with:
   ```python
   import sys
   sys.path.insert(0, '/home/YOURUSERNAME/hospify')

   from app import create_app
   application = create_app()
   ```
6. Click **Save**

### 1.6 Set Environment Variables
1. In the **Web** tab → **Environment variables** section
2. Click **Add environment variable** for each:

   | Variable | Value |
   |----------|-------|
   | `SECRET_KEY` | Run this in Bash: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `JWT_SECRET_KEY` | Run this in Bash: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `DEBUG` | `False` |
   | `DB_HOST` | `YOURUSERNAME.mysql.pythonanywhere-services.com` |
   | `DB_PORT` | `3306` |
   | `DB_USER` | `YOURUSERNAME` |
   | `DB_PASSWORD` | *(your MySQL password)* |
   | `DB_NAME` | `YOURUSERNAME$hospify_db` |
   | `CORS_ORIGINS` | `https://yourdomain.profreehost.com` |
   | `UPLOAD_FOLDER` | `/home/YOURUSERNAME/hospify/uploads` |

3. Click **Reload YOURUSERNAME.pythonanywhere.com**

### 1.7 Test
Visit: `https://YOURUSERNAME.pythonanywhere.com/api/health`
Expected: `{"status":"ok","app":"Hospify API","version":"1.0.0"}`

---

## Part 2: Frontend → ProFreeHost

### 2.1 Upload Frontend Files
1. ProFreeHost cPanel → **File Manager**
2. Go to `public_html/` (or your subdomain folder)
3. Upload ALL files and folders from `frontend/`

### 2.2 Configure API URL
Edit `public_html/js/config.js`:
```javascript
const HOSPIFY_CONFIG = {
  API_BASE_URL: 'https://YOURUSERNAME.pythonanywhere.com/api',
};
```

All pages (login, signup, dashboards) will use this URL automatically.

---

## Part 3: Login

- **Username**: `superadmin`
- **Password**: `Admin@1234`

**Change immediately after first login!**

---

## Project Structure (after cleanup)

```
Hospify2.0/
├── backend/              ← Upload to PythonAnywhere
│   ├── app.py
│   ├── config.py
│   ├── extensions.py
│   ├── seed_medicines.py
│   ├── wsgi.py
│   ├── passenger_wsgi.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   └── routes/
├── frontend/             ← Upload to ProFreeHost
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── css/
│   ├── js/
│   └── dashboards/
├── database/
│   └── hospify.sql
├── DEPLOYMENT.md
├── start.bat
└── .gitignore
```
