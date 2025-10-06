# Grocery Store - Django E-commerce Application

A Django-based e-commerce web application for a grocery store with multi-store inventory management, user authentication, shopping cart functionality, and geographical features.

## Project Structure

### F109 Client Management

    - Added paths to urls.py for profile page, edit profile page, login page and signup page
    - Added file for unit tests /tests/test_forms.py
    - Created profile.html, edit_profile.html, login.html, signup.html
    - Prepared Custom user registration inside forms.py
    - Added functions to views.py: authView(request) and profile(request) and edit_profile(request)

### F110 Staff Management

    - Staff page can be accessed via http://127.0.0.1:8000/admin/
    - admin.py is used for editing admin page where staff can edit User Details and etc.
    - Created class customer user admin for managing admin screen
    - Updated admin.py to use custom user admin class
    - Created custom_user_admin.py for staff to manage users like editing username, first and last name and email
    - Updated custom_user_admin.py to allow filtering and show list of users with respective details

### Commands to run

Database setup

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

Run the test suite:

```bash
python3 manage.py test
```

Run the project

```bash
python3 manage.py runserver
```

### Access Application

- Main site: `http://127.0.0.1:8000/`
