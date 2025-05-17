import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'notifications.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    EMAIL_ADDRESS = os.getenv("MAIL_USERNAME", "kshitij6102004@gmail.com")
    EMAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "ycxoaecbwfcnqqds")