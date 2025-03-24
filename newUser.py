from app import create_app
from app import db
from app.models import Employee, Ticket, Client, Places
app = create_app()
def add_employee():
    with app.app_context():  # Устанавливаем контекст приложения
        new_employee = Client(company_name='клиеент', username='client', telegram_id='7605039209')
        new_employee.set_password('12345')

        db.session.add(new_employee)
        db.session.commit()
        print("Сотрудник успешно добавлен!")

if __name__ == '__main__':
    add_employee()