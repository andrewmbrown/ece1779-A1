from flask import render_template, flash, redirect, url_for, request
from flask_migrate import current
from app import app, db
from app.forms import LoginForm, RegistrationForm
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User

'''
# This code is the driver/state of the app
# each function defines the behaviour of a certain part of the app
# performs logical functions then renders html display 
@app.route('/')  # decorator, modifies the function that follows it
'''


# To ensure we always have an admin account we attempt to make it every time
# in case there are no accounts
def setup():
    # function to attempt to create admin account every time the webapp is started
    # since at least one account needs administrator priveleges, it needs to exist
    try:
        admin = User(username='root', email='root@email.com')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        print("added admin,username: root, password: password")
    except:
        print("Admin user account already exists")


# fix this later
setup()  # configure admin account
@app.route('/')
@app.route('/index')  # use as register fxn as callbacks for certain events
@login_required
def index():
    # render_template() invokes jinja2 substituting {{...}} blocks with corresponding values
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Toronto!'
        },
        {
            'author': {'username': 'Mickey'},
            'body': 'Avengers is my favourite movie'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)


# @app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # only see anything if logged in
        flash("Currently logged in")
    else:
        return redirect(url_for('index'))
    if int(current_user.id) == 1 or str(current_user.username) == 'root':  # first account or root name
        flash("You have admin permissions")
    else:
        flash("Sorry, only administrators can register accounts")
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)