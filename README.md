# smart-queue-backend

Smart Queue Management system for government offices and service centers.
Service backend is built with **Django**.

---

## Prerequisites

Make sure to install the following:

- [Python3](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)
- Pipenv

Install Pipenv using python package manager:

```bash
pip install pipenv
```

---

## Getting Started

1. install dependencies

```bash
pipenv insall
pipenv shell
```

set your project's python environment to pipenv's

2. Create the database in MySQL

```sql
CREATE DATABASE smart_queue
```

3. Go to Django settings file

```bash
smart_queue/settings.py
```

Update the <mark>DATABASES</mark> Configuration with your local MySQL credentials

```py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "smart_queue",
        "HOST": "localhost",
        "USER": "root",
        "PASSWORD": "root",
    }
}
```

4. Run migrations to create the database schema

```bash
python manage.py migrate
```

5. Start the Server, in your python environment Run

```bash
python manage.py runserver
```

---

## Admin Panel

To access the Admin Panel, you must first create a superuser account:

```bash
python manage.py createsuperuser
```
