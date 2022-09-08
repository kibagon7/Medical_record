from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, static_folder='./assets')

heroku = 1

if heroku:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL_RE']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:yiishi@localhost:5432/medical_record'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "secretkey"

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=False, nullable=False)
    date = db.Column(db.String(30), unique=False, nullable=False)
    hospital = db.Column(db.String(30), unique=False, nullable=False)
    doctor = db.Column(db.String(10), unique=False, nullable=True)
    body = db.Column(db.String(1000), unique=False, nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(1000), unique=True, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def first():
    return render_template("first.html")

@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")


        user = User(username = username, password = generate_password_hash(password, method="sha256"))

        db.session.add(user)
        db.session.commit()
        
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user is None:
            return render_template("login_fail.html")

        if check_password_hash(user.password, password):
            login_user(user)
        else:
            return render_template("login_fail.html")
            
        return redirect("/home")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/record", methods=["GET", "POST"])
@login_required
def index():
    names = Record.query.filter_by(user_id = current_user.id)
    hos = []
    doc = []

    for i in names:
        hos.append(i.hospital)
    for i in names:
        doc.append(i.doctor)
    hospitals = set(hos)
    doctors = set(doc)

    if request.method == "GET":
        all_records = Record.query.filter_by(user_id = current_user.id).order_by(desc(Record.date)).all()

        return render_template("index.html", records = all_records, hospitals = hospitals, doctors = doctors)
    
    else:
        hospital = request.form.get("hospital")
        doctor = request.form.get("doctor")

        if hospital=="None" and doctor!="None":
            filtered_records = Record.query.filter_by(user_id = current_user.id, doctor=doctor).order_by(desc(Record.date)).all()

        elif hospital!="None" and doctor=="None":
            filtered_records = Record.query.filter_by(user_id = current_user.id, hospital=hospital).order_by(desc(Record.date)).all()

        elif hospital!="None" and doctor!="None":
            filtered_records = Record.query.filter_by(user_id = current_user.id, doctor=doctor, hospital=hospital).order_by(desc(Record.date)).all()

        else:
            filtered_records = Record.query.filter_by(user_id = current_user.id).order_by(desc(Record.date)).all()

        return render_template("index.html", records = filtered_records, hospitals = hospitals, doctors = doctors)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "GET":
        return render_template("create.html")
    else:
        user_id = current_user.id
        date = request.form.get("date")
        hospital = request.form.get("hospital")
        doctor = request.form.get("doctor")
        body = request.form.get("body")

        record = Record(user_id = user_id, date = date, hospital = hospital, 
                         doctor = doctor, body = body)

        db.session.add(record)
        db.session.commit()
        
        return redirect("/record")

@app.route("/edit/<int:id>", methods = ["GET", "POST"])
@login_required
def edit(id):
    record = Record.query.get(id)

    if request.method == "GET":
        return render_template("edit.html", record = record)
    else:
        record.date = request.form.get("date")
        record.hospital = request.form.get("hospital")
        record.doctor = request.form.get("doctor")
        record.body = request.form.get("body")
        
        db.session.commit()

        return redirect("/record")

@app.route("/delete/confirm/<int:id>", methods = ["GET", "POST"])
@login_required
def delete_confirm(id):
    record = Record.query.get(id)
    if request.method == "POST":
        if request.form.get("delornot") == "delete":
            db.session.delete(record)
            db.session.commit()

        return redirect("/record")
    
    else:
        return render_template("delete_confirm.html", record = record)