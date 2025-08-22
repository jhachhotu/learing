# E-Waste Management System

A web application for managing e-waste collection and processing.

## Features

- User authentication (signup, login, email verification)
- E-waste pickup request management
- Collection center management
- Processing center information
- Real-time tracking of pickup requests

## Prerequisites

- Python 3.9+
- PostgreSQL (for production)
- Git

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in a `.env` file
5. Initialize the database:
   ```bash
   flask db upgrade
   ```
6. Run the development server:
   ```bash
   python app.py
   ```

## Environment Variables

Create a `.env` file with the following variables:

```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
```

## Deployment on Render

1. Push your code to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New" and select "Web Service"
4. Connect your GitHub repository
5. Configure the following settings:
   - Name: ewaste-management (or your preferred name)
   - Region: Choose the one closest to your users
   - Branch: main (or your main branch)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. Add the following environment variables:
   - `PYTHON_VERSION`: 3.9.13
   - `FLASK_APP`: app.py
   - `FLASK_ENV`: production
   - `SECRET_KEY`: Generate a strong secret key
   - `JWT_SECRET_KEY`: Generate a strong JWT secret key
   - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Your email configuration
7. Click "Create Web Service"

## Database Setup on Render

1. In the Render Dashboard, click "New" and select "PostgreSQL"
2. Configure the database with a name and credentials
3. After creation, go to the database details and copy the external database URL
4. Add the database URL as an environment variable in your web service:
   - `DATABASE_URL`: postgresql://user:password@host:port/dbname

## License

This project is licensed under the MIT License.
