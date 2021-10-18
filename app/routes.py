from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm

'''
# NOTE: This is all placeholder code, it will be changed
@app.route('/')  # decorator, modifies the function that follows it
'''

# fix this later
@app.route('/')
def starter():
    return redirect(url_for('login'))

# @app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('login for user {}, remember={}'. format(
            form.user.data, form.remember.data
        ))
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)

@app.route('/index')  # use as register fxn as callbacks for certain events
def index():
    user = {'username': 'Andrew'}
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
    return render_template('index.html', title='Home', user=user, posts=posts)