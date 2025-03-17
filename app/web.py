from flask import Blueprint, Flask, jsonify, render_template, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

from flask import request
from flask import redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from .models import Employee, Ticket, Client, Places  # импорт моделей


web_bp = Blueprint('web', __name__)
login_manager = LoginManager()
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("employee-"):
        employee_id = user_id.split("-")[1]
        return db.session.query(Employee).get(employee_id)
    elif user_id.startswith("client-"):
        client_id = user_id.split("-")[1]
        return db.session.query(Client).get(client_id)
    return None

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        company_name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        role = 'client'

# добавить поля в этой функции, добавить поля для ввода на форме регистрации, добавить во вкладку с клиентами для сотрудников возможность рассмотрения новых пользователей
# для клиентов изменить base html. добавить клиентам вкладку профиля, создания новой заявки, и всех заявок.
        new_client = Client(company_name=company_name, username=username, role=role)
        new_client.set_password(password)

        db.session.add(new_client)
        db.session.commit()
        flash('Регистрация прошла успешно!')
        return redirect(url_for('web.login'))
    return render_template('register.html')


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        employee = Employee.query.filter_by(username=username).first()
        if employee and employee.check_password(password):
            login_user(employee)
            return redirect(url_for('web.tickets'))
        else:
            client = Client.query.filter_by(username=username).first()
            if client and client.check_password(password):
                login_user(client)
                print(f"user_id: {current_user.id}")  # Вывод значения user_id
                session['user_id'] = current_user.id
                return redirect(url_for('web.profile'))
        
        flash('Неверные имя пользователя или пароль.')
    return render_template('login.html')


@web_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('web.login'))

@web_bp.route('/')
@login_required
def home():
    return render_template('index.html')

@web_bp.route('/employees')
@login_required
def employees():
    currentUser = Employee.query.filter_by(id=current_user.id).first()
    currentUserRole = currentUser.role
    return render_template('employees.html', currentUserRole=currentUserRole)

@web_bp.route('/tickets')
@login_required
def tickets():
    employees = Employee.query.all()
    clients = Client.query.all()
    currentEmployee = Employee.query.filter_by(id=current_user.id).first()
    currentEmployeeName = currentEmployee.name
    return render_template('tickets.html', employees=employees, clients=clients, currentEmployeeName=currentEmployeeName)

@web_bp.route('/payments')
@login_required
def payments():
    clients = Client.query.all()
    tickets = Ticket.query.all()
    return render_template('payments.html', tickets=tickets, clients=clients)

@web_bp.route('/clients')
@login_required
def clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@web_bp.route('/profile')
@login_required
def profile():
    clients = Client.query.all()
    user = current_user.id
    return render_template('profile.html', clients=clients)



@web_bp.route('/myplaces', methods=['GET', 'POST'])
@login_required
def myplaces():
    if request.method == 'POST':
        address = request.form['address']
        admin_name = request.form['admin_name']
        admin_phone = request.form['admin_phone']

        # Создание новой точки
        new_place = Places(
            client_id=current_user.id,  # Используем текущий client_id
            address=address,
            admin_name=admin_name,
            admin_phone=admin_phone
        )
        db.session.add(new_place)
        db.session.commit()

    # Получение всех точек, принадлежащих текущему пользователю
    places = Places.query.filter_by(client_id=current_user.id).all()
    return render_template('myplaces.html', places=places)

# Удаление точки
@web_bp.route('/delete_place/<int:place_id>', methods=['POST'])
@login_required
def delete_place(place_id):
    place = Places.query.get_or_404(place_id)

    if place.client_id == current_user.id:  # Проверка, что точка принадлежит текущему пользователю
        db.session.delete(place)
        db.session.commit()

    return redirect(url_for('web.myplaces'))

@web_bp.route('/mytickets')
@login_required
def mytickets():
    clients = Client.query.all()
    tickets = Ticket.query.all()
    user_id = current_user.id
    places = Places.query.filter_by(client_id=current_user.id).all()
    return render_template('mytickets.html', tickets=tickets, clients=clients, user_id=user_id, places=places)


@web_bp.route('/link_telegram_account', methods=['POST'])
@login_required
def link_telegram_account():
    data = request.json
    telegram_id = data.get('telegram_id')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')

    # Получаем текущего клиента
    client = Client.query.filter_by(id=current_user.id).first()

    if client:
        # Привязываем Telegram ID к клиенту
        client.telegram_id = telegram_id

        db.session.commit()

        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Client not found'}), 404