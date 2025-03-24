from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import datetime
from app import db

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Новая')
    source = db.Column(db.String(50), nullable=False)  # 'email', 'site', 'manual'
    created_at = db.Column(db.String(50), default=datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'))
    started_at = db.Column(db.String(50))  # Дата взятия в работу
    completed_at = db.Column(db.String(50))  # Дата завершения
    type = db.Column(db.String(50), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'), nullable=True)  # Новое поле
    place = db.relationship('Places', backref=db.backref('tickets', lazy=True))

class Employee(UserMixin, db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'employee' или 'director'
    telegram_id = db.Column(db.String(50), nullable=True)
    def __repr__(self):
        return "<{}:{}>".format(self.id, self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,  password):
        return check_password_hash(self.password_hash, password)
    def get_id(self):
        return f"employee-{self.id}"

class Client(UserMixin, db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    telegram_id = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,  password):
        return check_password_hash(self.password_hash, password)
    def get_id(self):
        return f"client-{self.id}"

class Places(db.Model):
    __tablename__ = 'places'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    address = db.Column(db.String(255), nullable=False)
    admin_name = db.Column(db.String(255), nullable=False)
    admin_phone = db.Column(db.String(50), nullable=False)