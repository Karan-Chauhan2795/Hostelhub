# HostelHub

## Project Overview
A single-college hostel management system for administrators, wardens, and students.

## Installation
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations and start the server.

## Development Demo Credentials
DEVELOPMENT / DEMO ACCOUNTS ONLY — do not use these credentials in production.

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `admin123` | ADMIN |
| `warden` | `warden123` | WARDEN |
| `student` | `student123` | STUDENT |

Create or refresh these accounts with:

```bash
python manage.py seed_demo_data
```

## Folder Structure
- accounts
- dashboard
- students
- rooms
- bookings
- complaints
- leave_management
- visitors
- notices
- nova_ai
- reports
- settings_app

## Technology Stack
- Django
- Python
- SQLite
- HTML5
- Custom CSS
- Vanilla JavaScript
