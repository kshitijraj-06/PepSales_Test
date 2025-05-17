Here's the complete `README.md` file for your notification service in the requested format:

```markdown
# Notification Service

A Flask-based service for sending email, SMS, and in-app notifications with RabbitMQ queue processing.

## Features
- ✅ Send notifications via Email, SMS, and In-App
- ✅ RabbitMQ queue for async processing
- ✅ Automatic retries for failed notifications (3 attempts)
- ✅ SQLite database storage
- ✅ REST API endpoints

## File Structure
```
notification-service/
├── app.py             # Main application with all routes
├── tasks.py           # Worker process for notifications
├── models.py          # Database models (User, Notification)
├── config.py          # Configuration settings
├── requirements.txt   # Python dependencies
└── README.md          # This documentation
```

## API Documentation

### 1. Create User
`POST /users`
```json
{
  "email": "user@example.com",
  "phone": "+1234567890" (optional)
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "phone": "+1234567890",
  "created_at": "2023-09-20T12:00:00"
}
```

### 2. Send Notification
`POST /notifications`
```json
{
  "user_id": 1,
  "message": "Your order has shipped!",
  "type": "email|sms|in-app"
}
```

**Response:**
```json
{
  "message": "Notification queued successfully"
}
```

### 3. Get User Notifications
`GET /users/<user_id>/notifications`

**Response:**
```json
[
  {
    "id": 1,
    "message": "Your order has shipped!",
    "type": "email",
    "status": "sent",
    "created_at": "2023-09-20T12:05:00"
  }
]
```

## Setup Instructions

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start RabbitMQ**:
```bash
# On Linux/Mac
rabbitmq-server

# On Windows (via WSL or installed service)
rabbitmq-service start
```

3. **Run the services**:
```bash
# Terminal 1 - Start Flask app
python app.py

# Terminal 2 - Start worker
python tasks.py
```

## Configuration
Edit `config.py` with your settings:
```python
# Email Configuration
EMAIL_ADDRESS = "your@gmail.com"  # SMTP username
EMAIL_PASSWORD = "yourpassword"   # SMTP password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Database
SQLALCHEMY_DATABASE_URI = "sqlite:///notifications.db"

# RabbitMQ
RABBITMQ_HOST = "localhost"
```

## Testing the Service

1. Create a test user:
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

2. Send a notification:
```bash
curl -X POST http://localhost:5000/notifications \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"message":"Test message","type":"email"}'
```

3. Check notifications:
```bash
curl http://localhost:5000/users/1/notifications
```

## Requirements
- Python 3.7+
- RabbitMQ server
- Flask
- SQLAlchemy
- Pika (for RabbitMQ)
- smtplib (for email)

## Troubleshooting
- **"Table already exists" errors**: Delete `notifications.db` and restart
- **RabbitMQ connection issues**: Verify service is running (`rabbitmqctl status`)
- **Email failures**: Check SMTP credentials and enable "Less Secure Apps" if using Gmail

```

This README includes:
1. Clear feature list
2. File structure matching your original setup
3. Complete API documentation
4. Step-by-step setup instructions
5. Configuration guidance
6. Test examples
7. Troubleshooting tips

The format avoids the factory pattern and maintains your original project structure while being comprehensive. Let me know if you'd like any modifications!
