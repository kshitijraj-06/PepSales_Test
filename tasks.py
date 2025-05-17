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

class InAppNotificationService:
    @staticmethod
    def create_notification(user_id, message, notification_type='generic'):
        """Create and store an in-app notification"""
        try:
            notification = InAppNotification(
                user_id=user_id,
                message=message,
                notification_type=notification_type
            )
            db.session.add(notification)
            db.session.commit()
            return notification
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to create notification: {str(e)}")

    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read"""
        notification = InAppNotification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_user_notifications(user_id, unread_only=False):
        """Retrieve notifications for a user"""
        query = InAppNotification.query.filter_by(user_id=user_id)
        if unread_only:
            query = query.filter_by(is_read=False)
        return query.order_by(InAppNotification.created_at.desc()).all()

def process_notification(data):
    with current_app.app_context():
        try:
            # Create the main notification record
            notification = Notification(
                user_id=data['user_id'],
                message=data['message'],
                type=data['type'],
                status='processing'
            )
            db.session.add(notification)
            db.session.commit()

            # Handle in-app notifications specifically
            if data['type'] == 'in-app':
                InAppNotificationService.create_notification(
                    user_id=data['user_id'],
                    message=data['message'],
                    notification_type=data.get('subtype', 'generic')
                )
                notification.status = 'sent'

            # Handle other notification types
            elif data['type'] == 'email':
                EmailNotification().send(data['user_id'], data['message'])
                notification.status = 'sent'

            elif data['type'] == 'sms':
                SMSNotification().send(data['user_id'], data['message'])
                notification.status = 'sent'

            db.session.commit()
            return (True, None)

        except Exception as e:
            db.session.rollback()
            print(f"Error processing notification: {str(e)}")

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