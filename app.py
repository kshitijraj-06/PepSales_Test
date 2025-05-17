from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika, json
from datetime import datetime
from extensions import db
from models import User, Notification, InAppNotification

app = Flask(__name__)
app.config.from_object('config.Config')
db.init_app(app)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    if '@' not in data['email']:
        return jsonify({'error': 'Invalid email format'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409

    new_user = User(email=data['email'], phone=data.get('phone'))
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/notifications', methods=['POST'])
def send_notification():
    data = request.get_json()
    if not all(k in data for k in ['user_id', 'message', 'type']):
        return jsonify({'error': 'Missing required fields'}), 400
    if data['type'] not in ['email', 'in-app']:
        return jsonify({'error': 'Invalid notification type'}), 400

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='notifications')
        message = {
            'user_id': data['user_id'],
            'message': data['message'],
            'type': data['type'],
            'retry_count': 0
        }
        channel.basic_publish(exchange='', routing_key='notifications', body=json.dumps(message))
        connection.close()
        return jsonify({'message': 'Notification queued successfully'}), 202
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/notifications', methods=['GET'])
def get_user_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notifications])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
