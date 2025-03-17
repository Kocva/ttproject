from app import create_app
from app import db
from app.models import Employee, Ticket, Client, Places
app = create_app()
def create_tables():
    with app.app_context():
        print("Создаю таблицы...")
        db.create_all()
        print("Таблицы созданы!")
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

    