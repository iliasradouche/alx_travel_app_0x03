# ALX Travel App 0x03 - Asynchronous Background Processing

This project enhances the ALX Travel App by implementing asynchronous background processing using Celery with RabbitMQ as the message broker. The main feature added is an email notification system that sends booking confirmations without blocking the main request-response cycle.

## Features

- **Asynchronous Task Processing**: Background task execution using Celery
- **Email Notifications**: Automated booking confirmation emails
- **RabbitMQ Integration**: Message broker for reliable task queuing
- **Django Integration**: Seamless integration with Django REST framework

## Prerequisites

- Python 3.8+
- Django 5.2.4
- RabbitMQ Server
- SMTP Email Configuration

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alx_travel_app_0x03
```

### 2. Install Dependencies

```bash
pip install -r alx_travel_app_0x00/requirement.txt
```

### 3. Install and Start RabbitMQ

#### On Windows:
```bash
# Download and install RabbitMQ from https://www.rabbitmq.com/download.html
# Or using Chocolatey:
choco install rabbitmq

# Start RabbitMQ service
rabbitmq-service start
```

#### On macOS:
```bash
brew install rabbitmq
brew services start rabbitmq
```

#### On Ubuntu/Debian:
```bash
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

### 4. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Chapa Payment Configuration (if using)
CHAPA_SECRET_KEY=your-chapa-secret-key
CHAPA_PUBLIC_KEY=your-chapa-public-key
CHAPA_BASE_URL=https://api.chapa.co/v1
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Running the Application

### 1. Start Django Development Server

```bash
python manage.py runserver
```

### 2. Start Celery Worker

Open a new terminal and run:

```bash
celery -A alx_travel_app_0x00 worker --loglevel=info
```

### 3. (Optional) Start Celery Beat for Scheduled Tasks

```bash
celery -A alx_travel_app_0x00 beat --loglevel=info
```

### 4. (Optional) Monitor Tasks with Flower

```bash
pip install flower
celery -A alx_travel_app_0x00 flower
```

Access Flower dashboard at: http://localhost:5555

## API Endpoints

### Bookings
- `POST /api/bookings/` - Create a new booking (triggers email notification)
- `GET /api/bookings/` - List user's bookings
- `GET /api/bookings/{id}/` - Get booking details

### Listings
- `GET /api/listings/` - List all listings
- `POST /api/listings/` - Create a new listing
- `GET /api/listings/{id}/` - Get listing details

## Testing the Email Notification System

### 1. Create a Booking via API

```bash
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "listing": 1,
    "check_in": "2024-02-01",
    "check_out": "2024-02-05",
    "guests": 2
  }'
```

### 2. Check Celery Worker Logs

Monitor the Celery worker terminal for task execution logs:

```
[2024-01-15 10:30:45,123: INFO/MainProcess] Received task: listings.tasks.send_booking_confirmation_email[abc123]
[2024-01-15 10:30:45,456: INFO/ForkPoolWorker-1] Task listings.tasks.send_booking_confirmation_email[abc123] succeeded
```

### 3. Verify Email Delivery

Check the recipient's email inbox for the booking confirmation email.

## Celery Configuration

The Celery configuration is located in:
- `alx_travel_app_0x00/celery.py` - Main Celery configuration
- `alx_travel_app_0x00/settings.py` - Django settings for Celery
- `listings/tasks.py` - Task definitions

### Key Settings:

```python
# Broker Configuration
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_RESULT_BACKEND = 'rpc://'

# Task Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
```

## Available Tasks

### 1. Booking Confirmation Email
- **Task**: `send_booking_confirmation_email`
- **Trigger**: Automatically when a booking is created
- **Purpose**: Send confirmation email to the user

### 2. Payment Confirmation Email
- **Task**: `send_payment_confirmation_email`
- **Trigger**: After successful payment processing
- **Purpose**: Send payment confirmation to the user

### 3. Payment Failure Email
- **Task**: `send_payment_failure_email`
- **Trigger**: After failed payment processing
- **Purpose**: Notify user of payment failure

## Troubleshooting

### Common Issues:

1. **RabbitMQ Connection Error**
   - Ensure RabbitMQ server is running
   - Check firewall settings
   - Verify broker URL in settings

2. **Email Not Sending**
   - Check email configuration in `.env`
   - Verify SMTP credentials
   - Check spam folder

3. **Celery Worker Not Starting**
   - Ensure all dependencies are installed
   - Check for syntax errors in tasks.py
   - Verify Django settings module

### Logs and Monitoring:

- **Celery Worker Logs**: Monitor task execution
- **Django Logs**: Check for application errors
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **Flower Dashboard**: http://localhost:5555

## Production Deployment

For production deployment:

1. Use a process manager like Supervisor or systemd for Celery workers
2. Configure RabbitMQ with proper authentication
3. Use a dedicated email service (SendGrid, AWS SES, etc.)
4. Set up monitoring and alerting
5. Configure proper logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.