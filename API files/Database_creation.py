# based on tutorial: https://www.youtube.com/watch?v=z3YMz-Gocmw

from API import app,db

with app.app_context():
    db.create_all()