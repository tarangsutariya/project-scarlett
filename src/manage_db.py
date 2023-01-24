from app import create_app
from app import db
import sys


app = create_app()
if len(sys.argv)<2:
    print("operation not specified")
    exit()
if sys.argv[1]=="create":
    with app.app_context():
        db.create_all()
elif sys.argv[1]=="drop":
    with app.app_context():
        db.drop_all()
else:
    print("operation not specified")
