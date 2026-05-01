# based on tutorial: https://www.youtube.com/watch?v=z3YMz-Gocmw

from Database_specification import app, db

with app.app_context():
    db.drop_all() # remove current tables in database.db
    db.create_all() # create new tables in database.db