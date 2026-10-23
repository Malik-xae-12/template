# Project Setup & Execution Guide (`run.md`)

This document outlines the step-by-step procedure used to set up the virtual environment, install dependencies, configure the project, and run the Django application.

---

## 1. Prerequisites

- **Python Version**: Python 3.13 (or `>= 3.13`)
- **Operating System**: Windows (PowerShell)

---

## 2. Create & Activate Virtual Environment

From the project root directory (`kanad-bcp-django`):

```powershell
# Create virtual environment using Python 3.13
py -3.13 -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

> **Note**: If script execution is restricted in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
> ```

---

## 3. Install Dependencies

Upgrade `pip` and install all required packages from `requirements.txt`, along with `waitress` (for `run_server.py`):

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt waitress
```

---

## 4. Necessary Configuration & Code Fixes

The following adjustments were made to ensure error-free startup:

### A. Fix `patient_helper.py` Syntax Error
- **File**: `apps/medfiles/services/patient_helper.py`
- **Issue**: Unassigned variables (`tenant_id = `, `client_id = `, etc.) resulted in a `SyntaxError: invalid syntax` on module import.
- **Resolution**: Replaced bare assignments with environment variable lookups and safe fallbacks:
  ```python
  import os

  tenant_id = os.getenv("AZURE_TENANT_ID", "")
  client_id = os.getenv("AZURE_CLIENT_ID", "")
  client_secret = os.getenv("AZURE_CLIENT_SECRET", "")
  scope = [os.getenv("AZURE_SCOPE", "https://api.fabric.microsoft.com/.default")]
  ```


### D. Azure AD / Microsoft Authentication
The following variables are configured in `envs/.env.development`:
```env
AZURE_AD_TENANT_ID=
AZURE_AD_CLIENT_ID=
AZURE_CLIENT_SECRET=

MICROSOFT_TENANT=
MICROSOFT_CLIENT_ID=
MICROSOFT_SECRET=

HOST=localhost:38000
CSRF_TRUSTED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
```

> **Important (Azure Portal App Registration Redirect URI)**:
> In the Azure Entra ID portal under your App Registration (`25ad11d7-5885-4f0e-8424-919bf02e04eb`), the Redirect URI must match:
> ```
> http://localhost:3000/accounts/microsoft/login/callback/
> ```

---

## 5. Verify Database & Configuration

Django is pre-configured with SQLite (`USE_SQLITE=True` in `envs/.env.development`):

```powershell
# Verify system integrity
.venv\Scripts\python.exe manage.py check

# Check and apply migrations (if needed)
.venv\Scripts\python.exe manage.py showmigrations
.venv\Scripts\python.exe manage.py migrate
```

---

## 6. Run the Application

Start the server on port 3000 so it matches the Azure redirect URI:

### Option A: Django Development Server (Recommended for Development)
```powershell
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:3000
```

### Option B: Waitress WSGI Server
```powershell
.venv\Scripts\python.exe run_server.py
```

---

## 7. Accessing the Application

- **Application URL**: [http://localhost:3000/](http://localhost:3000/)
- **Login Page**: [http://localhost:3000/auth/login/](http://localhost:3000/auth/login/)
- **Microsoft Sign-in Callback**: `http://localhost:3000/accounts/microsoft/login/callback/`
- **Admin Panel**: [http://localhost:3000/admin/](http://localhost:3000/admin/)
