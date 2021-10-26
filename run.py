#!venv/bin/python
from app import app, db
#webapp.run()
# webapp.run(host='0.0.0.0')
from app.models import User, ImageLocation

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'ImageLocation': ImageLocation}