# smart-queue-backend

Smart Queue Management system for government offices and service centers.
Service backend is built with **Django**.

## Getting Started

### Prerequisites

Make sure to install the following:

- [Python3](https://www.python.org/downloads/)
- [MySQL Server](https://dev.mysql.com/downloads/mysql/)
- Pipenv

Install Pipenv using python package manager:

- pip
  ```bash
  pip install pipenv
  ```

### Installation

1. Clone the repo

   ```sh
   git clone https://github.com/ah00819/smart-queue-backend.git

   ```

2. Change git remote url to avoid accidental pushes to base project

   ```sh
   git remote set-url origin github_username/repo_name
   git remote -v # confirm the changes
   ```

3. install project dependencies

   ```sh
   pipenv install
   pipenv shell
   ```

   set your project's python environment to pipenv's

4. Create the database in MySQL

   ```sql
   CREATE DATABASE smart_queue
   ```

5. Go to Django settings file

   ```sh
   smart_queue/settings.py
   ```

   Update the `DATABASES` Configuration with your local MySQL credentials

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

6. Run migrations to create the database schema

   ```sh
   python manage.py migrate
   ```

7. Start the Server, in your python environment Run

   ```sh
   python manage.py runserver
   ```

---

## Admin Panel

To access the Admin Panel, you must first create a superuser account:

```sh
python manage.py createsuperuser
```
