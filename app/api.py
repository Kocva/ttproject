from flask import Blueprint, Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
import datetime
import requests

from flask import render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, Employee, Ticket, Client, Places  # импорт моделей
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

TELEGRAM_BOT_TOKEN = "7506782496:AAFa49IjW1q3wrO1e5L4QGmDpgVILI3vvq0"
# Модель заявки
# class Ticket(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     description = db.Column(db.String(200), nullable=False)
#     status = db.Column(db.String(20), default='новая')
#     created_at = db.Column(db.String(50), default=datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'))

# Инициализация базы данных
def create_tables():
    with api_bp.app_context():
        db.create_all()

TELEGRAM_BOT_USERNAME = "test_tt_irk_bot"  # Замени на имя твоего бота

@api_bp.route('/login', methods=['POST'])
def login():
    if request.content_type != "application/json":
        return jsonify({"error": "Неверный формат данных, используйте JSON"}), 415

    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Введите имя пользователя и пароль"}), 400

    user = Employee.query.filter_by(username=data["username"]).first()

    if user and user.check_password(data["password"]):
        session["user_id"] = user.id
        return jsonify({"message": "Успешный вход", "user_id": user.id})
    else:
        return jsonify({"error": data}), 401

@api_bp.route('/link_telegram_account', methods=['POST'])
def link_telegram_account():
    data = request.json
    telegram_id = data['telegram_id']
    client_id = data['client_id']  # ID клиента на веб-сайте

    # Ищем клиента по client_id
    client = Client.query.filter_by(id=client_id).first()
    
    if not client:
        return jsonify({'message': 'Клиент не найден'}), 404

    # Привязываем Telegram ID к клиенту
    client.telegram_id = telegram_id
    db.session.commit()

    return jsonify({'message': 'Телеграм аккаунт успешно привязан'}), 200



@api_bp.route('/client', methods=['POST'])
def add_client():
    data = request.json
    new_client = Client(company_name = data['company_name'], username = data['username'])
    new_client.set_password(data['password'])
    db.session.add(new_client)
    db.session.commit()
    return jsonify({'message': 'клиент добавлен'})

@api_bp.route('/clients', methods=['GET'])  # Используем GET метод для получения списка клиентов
def get_clients():
    # Получаем всех клиентов из базы данных
    clients = Client.query.all()
    
    # Преобразуем список клиентов в список словарей
    clients_data = [
        {'id': client.id, 'company_name': client.company_name, 'username': client.username}
        for client in clients
    ]
    
    # Возвращаем список клиентов в формате JSON
    return jsonify(clients_data)

@api_bp.route('/employee', methods=['GET'])
def get_employee():
    try:
        employees = Employee.query.all()
        result = [{'id': employee.id, 'name': employee.name, 'role': employee.role} for employee in employees]
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении заявок: {e}")
        return jsonify({'error': 'Ошибка при получении заявок'}), 500
    
@api_bp.route('/employee', methods=['POST'])
def addEmployee():
    data = request.json
    try:
        new_employee = Employee(name=data['name'], username=data['username'], role=data['role'], telegram_id=data['telegram'])
        new_employee.set_password(data['password'])

        db.session.add(new_employee)
        db.session.commit()
        return jsonify({'message': 'сотрудник добавлен'})
        
    except Exception as e:
        print(f"Ошибка при создании заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

@api_bp.route('/employee/<int:id>', methods=['DELETE'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    return jsonify({'message': 'сотрудник удален'})




# Получение всех заявок
@api_bp.route('/tickets', methods=['GET'])
def get_tickets():
    try:
        tickets = Ticket.query.join(Employee, Ticket.employee_id == Employee.id, isouter=True) \
                              .join(Client, Ticket.client_id == Client.id, isouter=True) \
                              .join(Places, Ticket.place_id == Places.id, isouter=True) \
                              .add_columns(
                                  Ticket.id, Ticket.title, Ticket.description, Ticket.status, Ticket.created_at,
                                  Employee.name.label('employee_name'), 
                                  Client.company_name.label('company_name'),
                                  Places.address.label('place_address')  # Добавляем address из таблицы Places
                              ) \
                              .all()
        
        result = [{
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status,
            'employee_name': ticket.employee_name,
            'company_name': ticket.company_name,
            'place_address': ticket.place_address,  # Добавляем place_address
            'created_at': ticket.created_at
        } for ticket in tickets]
        tickets2 = Ticket.query.all()
        print(f"Заявки, которые будут возвращены: {tickets2}")
        return jsonify(result)
    except Exception as e:
        print(f"Ошибка при получении заявок: {e}")
        return jsonify({'error': 'Ошибка при получении заявок'}), 500

# Создание новой заявки
@api_bp.route('/tickets', methods=['POST'])
def create_ticket():
    data = request.json
    if not data or not 'title' in data or not 'description' in data:
        return jsonify({'error': 'Неверные данные, необходимо указать title и description'}), 400
    
    print(f"Получены данные: {data}")
    
    try:
        # Добавление place_id при создании заявки
        place_id = data.get('place_id')  # Получаем place_id из данных
        new_ticket = Ticket(
            title=data['title'],
            description=data['description'],
            source=data['source'],
            employee_id=data['employee_id'],
            client_id=data['client_id'],
            place_id=place_id,  # Записываем place_id
            created_at=datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
        )
        print(f"Дата: {new_ticket.created_at}")
        db.session.add(new_ticket)
        db.session.commit()

        tickets = Ticket.query.all()
        print(f"Заявки в базе после добавления: {[ticket.title for ticket in tickets]}")
        return jsonify({'message': 'Заявка создана', 'ticket_id': new_ticket.id}), 201
    except Exception as e:
        print(f"Ошибка при создании заявки: {e}")
        return jsonify({'error': 'Ошибка при создании заявки'}), 500

# Изменение статуса заявки
@api_bp.route('/tickets/<int:id>', methods=['PATCH'])
def update_ticket(id):
    data = request.json
    ticket = Ticket.query.get_or_404(id)
    
    # Обновляем поля, если они присутствуют в запросе
    if 'status' in data:
        old_status = ticket.status
        ticket.status = data['status']
    if 'title' in data:
        ticket.title = data['title']
    if 'description' in data:
        ticket.description = data['description']
    
    db.session.commit()
    client = Client.query.get(ticket.client_id)
    if client.telegram_id != "":
        
        if client and client.telegram_id:
            message = f"🔔 Статус вашей заявки '{ticket.title}' изменился: {old_status} → {ticket.status}"
            send_telegram_notification(client.telegram_id, message)

    return jsonify({'message': 'Заявка обновлена'})

# Удаление заявки
@api_bp.route('/tickets/<int:id>', methods=['DELETE'])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Заявка удалена'})

@api_bp.route('/client/<int:client_id>/tickets', methods=['GET'])
def get_client_tickets(client_id):
    tickets = Ticket.query.filter_by(client_id=client_id).all()
    tickets_data = [
        {
            'id': ticket.id,
            'title': ticket.title,
            'description': ticket.description,
            'status': ticket.status
        }
        for ticket in tickets
    ]
    if tickets_data:
        return jsonify(tickets_data)
    else:
        return jsonify({'message': 'У вас нет заявок.'}), 404
    
@api_bp.route('/client_by_telegram/<int:telegram_id>', methods=['GET'])
def get_client_by_telegram(telegram_id):
    client = Client.query.filter_by(telegram_id=telegram_id).first()
    
    if client:
        return jsonify({'client_id': client.id})
    else:
        return jsonify({'message': 'Клиент не найден.'}), 404

@api_bp.route('/employee_by_telegram/<int:telegram_id>', methods=['GET'])
def get_employee_by_telegram(telegram_id):
    employee = Employee.query.filter_by(telegram_id=telegram_id).first()
    
    if employee:
        return jsonify({'employee_id': employee.id})
    else:
        return jsonify({'message': 'Сотрудник не найден.'}), 404

@api_bp.route('/places/<int:client_id>', methods=['GET'])
def get_client_places(client_id):
    

    # Получаем все точки для конкретного клиента из базы данных
    places = Places.query.filter_by(client_id=client_id).all()

    # Формируем данные для отправки
    places_data = [{
        'id': place.id,
        'address': place.address,
        'admin_name': place.admin_name,
        'admin_phone': place.admin_phone
    } for place in places]

    # Возвращаем список точек в формате JSON
        
    print(f"Заявки, которые будут возвращены: {places_data}")
    
    return jsonify(places_data)

@api_bp.route('/tickets/<int:ticket_id>/take', methods=['PATCH'])
def take_ticket(ticket_id):
    # Получаем заявку по ID
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'message': 'Заявка не найдена'}), 404

    # Проверяем, что заявка еще не в работе
    if ticket.status == 'В работе':
        return jsonify({'message': 'Заявка уже в работе'}), 400

    # Получаем текущего сотрудника из сессии (предполагаем, что это current_user)
    employee = current_user  # Текущий сотрудник, если он авторизован

    if not employee:
        return jsonify({'message': 'Вы не авторизованы'}), 401

    # Обновляем заявку: назначаем сотрудника и меняем статус на "В работе"
    ticket.employee_id = employee.id
    ticket.status = 'В работе'

    db.session.commit()

    return jsonify({
        'message': 'Заявка взята в работу',
        'ticket': {
            'id': ticket.id,
            'title': ticket.title,
            'status': ticket.status,
            'employee_name': employee.name
        }
    })
@api_bp.route('/clients/<int:client_id>/trade_points', methods=['GET'])
def get_trade_points(client_id):
    trade_points = Places.query.filter_by(client_id=client_id).all()
    return jsonify([{"id": point.id, "name": point.address} for point in trade_points])

def send_telegram_notification(telegram_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    return response.json()

@api_bp.route('/employee/<int:id>', methods=['PATCH'])
def update_employee(id):
    data = request.json
    employee = Employee.query.get_or_404(id)
    
    # Обновляем поля, если они присутствуют в запросе
    if 'name' in data:
        employee.name = data['name']
    if 'role' in data:
        employee.role = data['role']
    
    db.session.commit()
    return jsonify({'message': 'Заявка обновлена'})