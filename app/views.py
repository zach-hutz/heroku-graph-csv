# pylint: disable=no-member

from flask import render_template, request, redirect, g, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy  import SQLAlchemy
from wtforms.validators import InputRequired, Email, Length
import email_validator
from wtforms import StringField, PasswordField, BooleanField
from flask_wtf import FlaskForm 
from flask_bootstrap import Bootstrap

from app import app
import os
import csv
import pandas as pd
import json
import sqlite3
import stat
import time
import pathlib
import re


user_data_path = pathlib.Path(__file__).parent.absolute()
user_data_path = str(user_data_path) + "/"
user_data_path = user_data_path + "static/user_data/"

file_upload_path = pathlib.Path(__file__).parent.absolute()
file_upload_path = str(file_upload_path) + "/"
file_upload_path = file_upload_path + "static/file/uploads"

file_path = os.path.abspath(os.getcwd())+"\database.db"

app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = os.path.join('sqlite:///' + file_path)
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

data_arrays = []
json_data = json.dumps(data_arrays)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/', methods=["GET", "POST"])
def index():
    data = []
    if request.method == 'POST':
        if request.files:
            uploaded_file = request.files['filename']
            filepath = os.path.join(app.config['FILE_UPLOADS'], uploaded_file.filename)

            if current_user.get_id() is not None:
                str_id = str(current_user.get_id())
                usr_fp = os.path.join(user_data_path + str_id, uploaded_file.filename)
                if uploaded_file.filename != "":
                    uploaded_file.save(usr_fp)
            else:
                if uploaded_file.filename != "":
                    uploaded_file.save(filepath)

            if current_user.get_id() is None:
                if uploaded_file.filename != "":
                    with open(filepath) as file:
                        csv_file = csv.reader(file)
                        for row in csv_file:
                            data.append(row)
            else:
                usr_fp = os.path.join(user_data_path + str_id, uploaded_file.filename)
                if uploaded_file.filename != "":
                    with open(usr_fp) as file:
                        csv_file = csv.reader(file)
                        for row in csv_file:
                            data.append(row)
                            
            data = pd.DataFrame(data[1:], columns=data[0])
            d_list = list(data.columns.values)

            x_label = d_list[0]
            y_label = d_list[1]

            data_x_array = list(data[x_label])
            data_y_array = list(data[y_label])
            data_y_array = [i.replace(" ", "") for i in data_y_array]
            data_y_array = [float(i) for i in data_y_array]

            ydump = json.dumps(data_y_array)
            xdump = json.dumps(data_x_array)

            data_arrays = []
            for col in d_list:
                data_arrays.append(list(data[col]))
            data_arrays = data_arrays[1:]
            json_data = json.dumps(data_arrays)

            colname = json.dumps(d_list)

            horiz_data = pd.DataFrame(data_arrays)
            horiz_array = []
            for i in range(0, len(horiz_data.iloc[:, 0])):
                horiz_array.append(list(horiz_data.iloc[:, i]))

            horiz_array_dumps = json.dumps(horiz_array)

            return render_template('index.html', horiz_array=horiz_array_dumps, columname=colname, json_data=json_data, y_label=y_label, datayarray=ydump, dataxarray=xdump, tables=[data.to_html(classes='data')], titles=str(data.iloc[0]), header=False, index=False, index_names=False)

        elif request.form['javascript_data'] != "":
            desired_file = request.form['javascript_data'].strip()
            with open(desired_file) as file:
                csv_file = csv.reader(file)
                for row in csv_file:
                    data.append(row)

            data = pd.DataFrame(data[1:], columns=data[0])
            d_list = list(data.columns.values)

            x_label = d_list[0]
            y_label = d_list[1]

            data_x_array = list(data[x_label])
            data_y_array = list(data[y_label])
            data_y_array = [i.replace(" ", "") for i in data_y_array]
            data_y_array = [float(i) for i in data_y_array]

            ydump = json.dumps(data_y_array)
            xdump = json.dumps(data_x_array)

            data_arrays = []
            for col in d_list:
                data_arrays.append(list(data[col]))
            data_arrays = data_arrays[1:]
            json_data = json.dumps(data_arrays)

            colname = json.dumps(d_list)

            horiz_data = pd.DataFrame(data_arrays)
            horiz_array = []
            for i in range(0, len(horiz_data.iloc[:, 0])):
                horiz_array.append(list(horiz_data.iloc[:, i]))

            horiz_array_dumps = json.dumps(horiz_array)

            return render_template('index.html', horiz_array=horiz_array_dumps, columname=colname, json_data=json_data, y_label=y_label, datayarray=ydump, dataxarray=xdump, tables=[data.to_html(classes='data')], titles=str(data.iloc[0]), header=False, index=False, index_names=False)
    return render_template('index.html', data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                str_id = str(current_user.get_id())
                absolute_path = os.path.abspath(__file__)
                if os.path.exists(os.path.join(os.path.dirname(absolute_path) + "\\static\\user_data", str_id)) == False:
                    os.mkdir(os.path.join(os.path.dirname(absolute_path) + "\\static\\user_data", str_id), mode=0o777)
                    os.chmod(os.path.join(os.path.dirname(absolute_path) + "\\static\\user_data", str_id), stat.S_IWRITE)
                return redirect('/')

        return '<h1>Invalid username or password</h1>'
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return render_template("index.html")
    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    files_in_dir = 0
    user_id = "0"
    user_id_list = list(user_id)
    user_id_list_dump = json.dumps(user_id_list)
    fix_directory = ''
    
    files_in_dir_dump = json.dumps(files_in_dir)
    file_names_in_dir_dump = json.dumps(files_in_dir)

    if current_user.get_id() is not None:
        user_id = str(current_user.get_id())
        user_id_list = list(user_id)
        user_id_list_dump = json.dumps(user_id_list)
        print(user_id_list_dump)
        str_id = str(current_user.get_id())
        directory = os.path.join(user_data_path,str_id)
        fix_directory = os.path.join(user_data_path,str_id + "\\")



        files_in_dir = next(os.walk(directory))[2]
        files_in_dir_dump = json.dumps(len(files_in_dir))
        file_names_in_dir_dump = json.dumps(files_in_dir)


    files_in_dir_dump = json.dumps(len(files_in_dir))
    file_names_in_dir_dump = json.dumps(files_in_dir)
    
    dir_dump = json.dumps(fix_directory)

    return render_template('dashboard.html', userpath=dir_dump, name=current_user.username, dir_names=file_names_in_dir_dump, dir_length=files_in_dir_dump)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("logout.html")

@app.route('/help')
def help():
    return render_template('help.html')


app.config['FILE_UPLOADS'] = file_upload_path