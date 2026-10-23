# Application Template

<div align="center">

![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Azure](https://img.shields.io/badge/azure-%230072C6.svg?style=for-the-badge&logo=microsoftazure&logoColor=white)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

</div>

## Prerequisites

- Windows, Mac or Linux
- Python >= 3.7
- setuptools, pip
- Git (Version Control)

## Technology Stack

- **BackEnd**
    - Django >= 4.0
- **Database**
    - sqlite (development), MS SQL Server (production/dev)
- **FrontEnd**
    - HTML5
    - CSS3
    - Bootstrap 5
    - jQuery + additional plugins
    - JavaScript (Interaction)

## Features/Modules

- Azure AD Authentication for organization.
- Automated Mail Functionality.
- Review Board for Coding Questions.
- Questions View and Export Functionality.
- Question Bank
- Integrated with Azure for storing Media Files (Screen Captured)
- CLI Commands for automating Data Ingestion.
- User Friendly (interactive) Assesment Page.
- Efficient Logging Mechanism.
- Secured Authentication using Django Build in Auth Mechanism.
- Report Generation
- Visual Dashboards (Not started).

### Windows

If you don't already have 3.9 installed (64-bit), you can get Python from [python.org](https://python.org).

For Git, we recommend [Git for Windows](https://git-scm.com/download/win) or [GitHub for Windows](https://desktop.github.com/). If you use Visual Studio/Visual Studio Code, you can use the integrated Git support.

### Mac/Linux

You should have Python and Git already installed, but make sure you have Python 3.9 (Recommended).

## Application Overview

### Git repository contents

Here's an overview of the files you'll find in the initial Git repository, which we'll clone in the next section.

**Will be added soon**

  
Main sources for the application. Consists of 3 pages (index, about, contact) with a master layout. Static content and scripts include bootstrap, jquery, modernizr and respond.

    \manage.py

Local management and development server support. Use this to run the application locally, synchronize the database, etc.

    \db.sqlite3

## Web app development - Windows - command line

### Clone the repository

First, clone the repository using the below steps.

```sh
git clone https://github.com/uiprojects/django-bootstrap-template.git
cd django-bootstrap-template
```

### Create virtual environment

We'll create a new virtual environment for development purposes (do not add it to the repository). Virtual environments in Python are not relocatable, so every developer working on the application will create their own locally.

```sh
    python -m venv venv
```

Install any external packages required by your application. You can use the requirements.txt file at the root of the repository to install the packages in your virtual environment:

```sh
   pip install -r requirements.txt
```

## Python Packages Information

    Django # Powerfull framework for Web Development using Python

    whitenoise # static files manager

    django-environ # read environment variables

    flake8 # code guidelines

    gunicorn # WSGI handler must be used in production

    coverage # Code coverage tool

    Pillow # Image/Video processing Library

    arrow # python date/time handler like momentjs

    mssql-django # Microsoft SQL DB Connector

    django-storages[azure]  # Azure SDK for connecting with Azure Blob Storage

    django-import-export # Import or export data from Admin panel

    django-admin-interface # Many Themes for Admin panel

    django-filter # Django Filter functionality

    django-widget-tweaks # for forms rendering

    django-ckeditor # rich text editor

    django-simple-history # Store History data

    django-debug-toolbar # Debug Toolbar

    django-extensions # Django Library Extensions

    # https://github.com/CristiFati/Prebuilt-Binaries/blob/master/PyGraphviz/v1.7/pygraphviz-1.7-cp39-cp39-win_amd64.whl?raw=true 

    django-compressor # Compress css and js files

    django-allauth # For third parth authentication like google,microsoft etc.
    

### Create a superuser

The database included with the application does not have any superuser defined. In order to use the sign-in functionality in the application, or the Django admin interface (if you decide to enable it), you'll need to create a superuser.

Run this from the command-line from your project folder:

```sh
   python manage.py createsuperuser
```

Follow the prompts to set the user name, password, etc.

### Run using development server

You can launch the application under a development server with the following command:

```sh
   python manage.py runserver --settings=OnlineTestApplication.settings.testing
```

The console will display the URL and port the server listens to: http://localhost:8000

Then, open your web browser to that URL.

## Using a Database

The database that is included with the application is a sqlite database. This is a convenient and useful default database to use for development, as it requires almost no setup. The database is stored in the db.sqlite3 file in the project folder.

Azure provides database services which are easy to use from a Django application. Tutorials for using [SQL Database] and [MySQL] from a Django application show the steps necessary to create the database service, change the database settings in [settings.py](./root/settings.py), and the libraries required to install.

Of course, if you prefer to manage your own database servers, you can do so using Windows or Linux virtual machines running on Azure.


## Django Admin Interface

Once you start building your models, you'll want to populate the database with some data. An easy way to do add and edit content interactively is to use the Django administration interface.

The code for the admin interface is commented out in the application sources, but it's clearly marked so you can easily enable it (search for 'admin').

After it's enabled, synchronize the database, run the application and navigate to `/admin`.

## Give a Star! :star:
If you liked the project or if this project helped you, please **give a star**. And also please **fork** this repository and send us **pull-requests**. If you find any problem please open **issue**.

> Did the sample not work for you as expected? Did you encounter issues trying this sample? Then please reach out to us using the [GitHub Issues](../../issues) page.

## Feedback

If you have any feedback, please reach out to us at nanthakumar.j@ubtiinc.com

<div style="background-color: white">

![Logo](https://149510500.v2.pressablecdn.com/wp-content/uploads/2020/11/UBTI-Logo_Secondary-02.png)

</div>

