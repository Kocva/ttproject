from app import create_app
from app import db
from app.models import Employee, Ticket, Client, Places
app = create_app()
def add_employee():
    with app.app_context():  # Устанавливаем контекст приложения
        new_employee = Employee(name='директор', username='Director', role='director', telegram_id='7900697501')
        new_employee.set_password('12345')

        db.session.add(new_employee)
        db.session.commit()
        print("Сотрудник успешно добавлен!")

if __name__ == '__main__':
    add_employee()