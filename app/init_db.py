from app.models import db
from app.api import app

app.config.from_object('app.config.Config')

with app.app_context():
    db.init_app(app)
    db.create_all()