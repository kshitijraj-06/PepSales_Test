import pika
import json
import time
from extensions import db
from models import User, InAppNotification, Notification
import smtplib
from email.message import EmailMessage
from config import Config

from flask import current_app  # Use current_app instead of importing app

MAX_RETRIES = 3


class EmailNotification:
    def send(self, user_id, message):
        msg = EmailMessage()
        msg.set_content(message)
        msg["Subject"] = "New Notification"
        msg["From"] = Config.EMAIL_ADDRESS
        msg["To"] = self._get_user_email(user_id)

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_ADDRESS, Config.EMAIL_PASSWORD)
            server.send_message(msg)

    def _get_user_email(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user.email


class SMSNotification:
    def __init__(self):
        # Initialize Twilio client here if needed
        pass

    def send(self, user_id, message):
        # Simulate SMS sending (replace with Twilio in production)
        print(f"Sending SMS to user {user_id}: {message}")
        time.sleep(1)
        if "fail" in message:
            raise Exception("Failed to send SMS")


class InAppNotification:
    def send(self, user_id, message):
        notification = InAppNotification(
            user_id=user_id,
            message=message
        )
        db.session.add(notification)
        db.session.commit()


def process_notification(data):
    # Use Flask's current_app context
    with app.app_context():
        notification = Notification(
            user_id=data['user_id'],
            message=data['message'],
            type=data['type'],
            status='processing'
        )
        db.session.add(notification)
        db.session.commit()

        try:
            if data['type'] == 'email':
                # Pass user_id and message
                EmailNotification().send(data['user_id'], data['message'])
            elif data['type'] == 'sms':
                SMSNotification().send(data['user_id'], data['message'])
            elif data['type'] == 'in-app':
                InAppNotification().send(data['user_id'], data['message'])

            notification.status = 'sent'
            db.session.commit()

        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()  # Rollback on error

            if data['retry_count'] < MAX_RETRIES - 1:
                data['retry_count'] += 1
                return (False, data)
            else:
                notification.status = 'failed'
                db.session.commit()

        return (True, None)


def start_worker():
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()
    channel.queue_declare(queue='notifications')

    def callback(ch, method, properties, body):
        data = json.loads(body)
        print(f"Processing notification: {data}")
        success, retry_data = process_notification(data)

        if not success and retry_data:
            ch.basic_publish(
                exchange='',
                routing_key='notifications',
                body=json.dumps(retry_data)
            )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue='notifications',
        on_message_callback=callback
    )
    print('Worker started. Waiting for messages...')
    channel.start_consuming()


if __name__ == '__main__':
    from app import app  # <-- Import your actual app instance

    with app.app_context():
        db.create_all()
    start_worker()