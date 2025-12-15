# Employee Management System

An **Employee Management System (EMS)** built with **Django** to manage employee and company records efficiently. The system supports full **CRUD (Create, Read, Update, Delete)** operations and follows a **role-based access model**, where administrators can manage all employee-related data.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge\&logo=python\&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge\&logo=django\&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge\&logo=bootstrap\&logoColor=white)
![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=for-the-badge\&logo=mysql\&logoColor=white)

---

## Features

* **Add Employee** – Admins can add new employees to the system.
* **View Employee Details** – View a complete list of employee records.
* **Update Employee Details** – Edit and update employee information.
* **Delete Employee** – Remove employee records from the database.

> This application is developed using **Python, Django, HTML/CSS, and Bootstrap**.



## Installation

### Prerequisites

* [Python](https://www.python.org/) **v3.8+**
* [Django](https://www.djangoproject.com/) **v4.0.4+**
* MySQL Server

---

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Configure Database

Update the **`settings.py`** file with your MySQL database credentials:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # 'NAME': BASE_DIR / 'db.sqlite3',
        'NAME': 'newemp',  # Your database (schema) name
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '3306'
    }
}
```

---

### 3. Apply Migrations

```bash
python manage.py migrate
```

---

### 4. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and navigate to:

```
http://127.0.0.1:8000/
```

---

## Contribution Guidelines

* Create a new branch for your changes
* Do not push directly to `main`
* Open a Pull Request for review

---

## License

This project is intended for **educational and learning purposes**.
