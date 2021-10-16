from flask import render_template
from app import app

# NOTE: This is all placeholder code, it will be changed
@app.route('/')  # decorator, modifies the function that follows it
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