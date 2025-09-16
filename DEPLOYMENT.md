# ALX Travel App Deployment Guide

This guide provides step-by-step instructions for deploying the ALX Travel App to production cloud platforms.

## Prerequisites

- Git repository with your code
- Email account for SMTP configuration
- RabbitMQ service (CloudAMQP for cloud deployment)

## Option 1: Deploy to Render (Recommended)

### Step 1: Prepare Your Repository

1. Ensure all files are committed to your Git repository:
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

### Step 2: Set Up RabbitMQ (CloudAMQP)

1. Go to [CloudAMQP](https://www.cloudamqp.com/)
2. Sign up for a free account
3. Create a new instance (Little Lemur - Free plan)
4. Copy the AMQP URL from your instance dashboard

### Step 3: Deploy to Render

1. Go to [Render](https://render.com/) and sign up
2. Connect your GitHub repository
3. Create a new **Web Service**:
   - **Name**: `alx-travel-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r alx_travel_app/requirement.txt`
   - **Start Command**: `gunicorn alx_travel_app.wsgi:application`
   - **Instance Type**: Free

### Step 4: Configure Environment Variables

In Render dashboard, add these environment variables:

```
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.onrender.com
DATABASE_URL=sqlite:///db.sqlite3
CELERY_BROKER_URL=amqp://your-cloudamqp-url
CELERY_RESULT_BACKEND=rpc://
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Step 5: Deploy Celery Worker

1. Create a new **Background Worker** in Render:
   - **Name**: `alx-travel-celery-worker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r alx_travel_app/requirement.txt`
   - **Start Command**: `celery -A alx_travel_app worker --loglevel=info`
   - Use the same environment variables as the web service

## Option 2: Deploy to PythonAnywhere

### Step 1: Upload Your Code

1. Sign up at [PythonAnywhere](https://www.pythonanywhere.com/)
2. Open a Bash console
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

### Step 2: Set Up Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r alx_travel_app/requirement.txt
```

### Step 3: Configure Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Create a new web app:
   - **Python version**: 3.11
   - **Framework**: Manual configuration
3. Set the source code path: `/home/yourusername/your-repo`
4. Set the working directory: `/home/yourusername/your-repo`
5. Edit the WSGI file to point to your Django app:
   ```python
   import os
   import sys
   
   path = '/home/yourusername/your-repo'
   if path not in sys.path:
       sys.path.append(path)
   
   os.environ['DJANGO_SETTINGS_MODULE'] = 'alx_travel_app.settings'
   
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

### Step 4: Configure Environment Variables

Create a `.env` file in your project root:

```bash
echo 'SECRET_KEY=your-secret-key' >> .env
echo 'DEBUG=False' >> .env
echo 'ALLOWED_HOSTS=yourusername.pythonanywhere.com' >> .env
# Add other environment variables...
```

### Step 5: Set Up Database

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Step 6: Configure Celery (Tasks)

For PythonAnywhere, you'll need to use their **Tasks** feature:

1. Go to **Tasks** tab
2. Create a new task:
   - **Command**: `cd /home/yourusername/your-repo && source venv/bin/activate && celery -A alx_travel_app worker --loglevel=info`
   - **Hour**: Leave blank for always running
   - **Minute**: Leave blank for always running

## Post-Deployment Steps

### 1. Test Swagger Documentation

Visit: `https://your-app-url/swagger/`

You should see the interactive API documentation.

### 2. Test API Endpoints

```bash
# Test listings endpoint
curl https://your-app-url/api/listings/

# Test bookings endpoint (requires authentication)
curl -H "Authorization: Bearer your-token" https://your-app-url/api/bookings/
```

### 3. Test Email Notifications

1. Create a booking through the API
2. Check Celery worker logs
3. Verify email delivery

## Troubleshooting

### Common Issues:

1. **Static files not loading**:
   - Run `python manage.py collectstatic`
   - Check `STATIC_ROOT` and `STATIC_URL` settings

2. **Database errors**:
   - Run migrations: `python manage.py migrate`
   - Check database URL configuration

3. **Celery tasks not running**:
   - Verify RabbitMQ connection
   - Check worker logs
   - Ensure environment variables are set

4. **Email not sending**:
   - Check SMTP credentials
   - Verify email configuration
   - Check spam folder

### Monitoring and Logs:

- **Render**: Check logs in the dashboard
- **PythonAnywhere**: Use error logs and server logs
- **Celery**: Monitor worker output

## Security Considerations

1. Use strong, unique secret keys
2. Enable HTTPS in production
3. Set proper CORS origins
4. Use environment variables for sensitive data
5. Regular security updates

## Performance Optimization

1. Use a proper database (PostgreSQL) for production
2. Configure caching (Redis)
3. Set up CDN for static files
4. Monitor application performance
5. Scale Celery workers as needed

## Support

For issues and questions:
1. Check the application logs
2. Review Django and Celery documentation
3. Check platform-specific documentation (Render/PythonAnywhere)