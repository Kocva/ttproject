from app import create_app
from app import db
from app.models import Employee, Ticket, Client, Places
app = create_app()
def add_employee():
    with app.app_context():
        client = Client.query.get(1)
        client.telegram_id = 7605039209
        db.session.commit()

if __name__ == '__main__':
    add_employee()