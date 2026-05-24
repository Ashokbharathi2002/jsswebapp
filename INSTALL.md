# Jothi Solar Solutions — Installation & Command Reference

A Django-based solar project management system with role-based dashboards for Super Users, Admins, Staff, Employees, and Customers.

---

## 📋 Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| pip | Latest | Bundled with Python |
| Git | Any | https://git-scm.com/ |

---

## ⚡ Every Day — Start the Project (Quick Reference)

> Run these commands **every time** you open a new terminal to work on the project.

### Step 1 — Navigate to the project folder

```cmd
cd "e:\jss be"
```

### Step 2 — Activate the Virtual Environment

**Windows — Command Prompt (cmd):**
```cmd
venv\Scripts\activate
```

**Windows — PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

> ✅ You will see `(venv)` appear at the start of your prompt — this means the environment is active.

### Step 3 — Start the Server

```cmd
python manage.py runserver
```

> 🌐 Open your browser and go to: **http://127.0.0.1:8000**

### Step 4 — Stop the Server

Press `Ctrl + C` in the terminal to stop the server.

### To Deactivate the Virtual Environment

```cmd
deactivate
```

---

## 🚀 Installation (First Time Setup)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd "jss be"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

> ✅ You should see `(venv)` at the start of your terminal prompt.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Seed the Super User Account

```bash
python seed_data.py
```

> This creates the default Super User:
> - **Username:** `superuser`
> - **Password:** `solar123`

### 7. Start the Development Server

```bash
python manage.py runserver
```

Visit: **http://127.0.0.1:8000**

---

## 🔧 Common Development Commands

### Run the Server

```bash
python manage.py runserver
```

Run on a custom port:
```bash
python manage.py runserver 8080
```

---

### Database Management

| Task | Command |
|------|---------|
| Create new migrations | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Show migration status | `python manage.py showmigrations` |
| Reset & re-seed data | `python manage.py flush` then `python seed_data.py` |

---

### User Management

| Task | Command |
|------|---------|
| Create Django superuser | `python manage.py createsuperuser` |
| Open Django shell | `python manage.py shell` |

---

### Static Files

```bash
python manage.py collectstatic
```

---

### Run Unit Tests

Run all tests:
```bash
python manage.py test
```

Run tests for a specific app:
```bash
python manage.py test core
```

Run a single test class:
```bash
python manage.py test core.tests.ComplaintTests
```

Run with verbose output:
```bash
python manage.py test --verbosity=2
```

---

### Admin Panel

Access the built-in Django admin panel at:

```
http://127.0.0.1:8000/admin/
```

> Login with the super user credentials (`superuser` / `solar123`).

---

## 👤 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Super User | `superuser` | `solar123` |

> All other accounts (Admins, Staff, Employees, Customers) are created through the application dashboards and require approval.

---

## 📁 Project Structure

```
jss be/
├── core/                    # Main Django app
│   ├── migrations/          # Database migration files
│   ├── templates/core/      # HTML templates for all dashboards
│   ├── models.py            # Database models (User, Project, Attendance, Complaint)
│   ├── views.py             # Business logic and dashboard views
│   ├── forms.py             # Django forms
│   ├── urls.py              # URL routing
│   └── tests.py             # Automated unit tests (18 tests)
├── jss_be/                  # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── seed_data.py             # Script to seed the super user account
├── manage.py                # Django management entry point
├── requirements.txt         # Python dependencies
└── INSTALL.md               # This file
```

---

## 🔑 Role Permissions Summary

| Feature | Customer | Employee | Staff | Admin | Super User |
|---------|----------|----------|-------|-------|------------|
| View own projects | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mark attendance | ❌ | ✅ | ✅ | ✅ | ✅ |
| Submit complaints | ✅ | ❌ | ❌ | ❌ | ❌ |
| View complaints | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage employees | ❌ | ❌ | ❌ | ✅ | ✅ |
| Close projects | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete users | ❌ | ❌ | ❌ | ❌ | ✅ |
| Approve accounts | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## ⚠️ Troubleshooting

### `ModuleNotFoundError`
Make sure your virtual environment is **activated** before running any commands.

### `django.db.utils.OperationalError: no such table`
Run migrations:
```bash
python manage.py migrate
```

### Port already in use
Use a different port:
```bash
python manage.py runserver 8080
```

### PowerShell script execution blocked
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📦 Saving Dependencies

After installing a new package:
```bash
pip freeze > requirements.txt
```

---

*Jothi Solar Solutions — Internal Management System*
