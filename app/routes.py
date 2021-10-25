import os
import time
import requests
import urllib.request
import shutil
from flask import render_template, flash, redirect, url_for, request
from flask_mail import Mail, Message
from flask_migrate import current
from app import app, db
from app.forms import LoginForm, RegistrationForm, RecoveryForm, PictureForm, URLPictureForm
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, ImageLocation
from wand.image import Image
from app.imagetransform import image_transform
from app.apputilities import extension_dict, check_img_url

'''
# This code is the driver/state of the app
# each function defines the behaviour of a certain part of the app
# performs logical functions then renders html display 
@app.route('/')  # decorator, modifies the function that follows it
'''


# To ensure we always have an admin account we attempt to make it every time
# in case there are no accounts
# email must be setup with a gmail that has proper permissions (passwords) and for emailing using 3rd party code
def setup():
    # function to attempt to create admin account every time the webapp is started
    # since at least one account needs administrator priveleges, it needs to exist
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'email@email.com'  # set this yourself
    app.config['MAIL_PASSWORD'] = 'my_password'  # set this yourself
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # <10MB server side validation
    mail = Mail(app)
    """
    msg = Message('Password Recovery', sender = 'andrewm.brown@mail.utoronto.ca', recipients = [user_email])
    msg.body = f"Hello, {user_name}, here is your password recovery:"
    mail.send(msg)
    flash("Sent password to your email!")
    """
    try:
        admin = User(username='root', email='root@email.com')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        print("added admin,username: root, password: password")
    except:
        print("Admin user account already exists")
    return mail


# fix this later
mail = setup()  # configure admin account and setup mail
@app.route('/')
@app.route('/index')  # use as register fxn as callbacks for certain events
@login_required
def index():
    # render_template() invokes jinja2 substituting {{...}} blocks with corresponding values
    admin_info = [
        {
            'author': {'username': 'the admin (root)'},
            'body': 'Please click on Upload to upload and image, and Gallery to see your current images!'
        }
    ]
    return render_template('index.html', title='Home', adminmsgs=admin_info)


# @app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    # no need to login if you're already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # form object of a login form class
    form = LoginForm()
    if form.validate_on_submit():  # method of this class to validate form
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            # check to see validity for username, if not valid try againn
            flash('Invalid username or password')
            return redirect(url_for('login'))
        # if valid, login the user
        login_user(user, remember=form.remember_me.data)
        # after logging in, attempt to direct app to the next page
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash("Successfully logged out")
    return redirect(url_for('index'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:  # only see anything if logged in
        flash("Currently logged in")
    else:
        flash("Please login, only administrators can register accounts")
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


@app.route('/recover', methods=['GET', 'POST'])
def recover():
    # function to reset users passwords using username and email
    form = RecoveryForm()
    if form.validate_on_submit():
        try:
            # First find the account
            user_name = str(form.username.data)  # enter username for security theatre
            user_email = str(form.email.data)
            user = User.query.filter_by(email=user_email).first()
            
            # set new password and commit it to db
            user.set_password(form.newpassword.data)
            db.session.add(user)
            db.session.commit()

            flash("Successfully changed password, please login!")
        except:
            flash("Unable to find account, please contact administrator")
        return redirect(url_for('index'))
    return render_template('recover.html', title='Recover Password', form=form)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        flash('Please login to upload images', category='danger')
        return redirect(url_for('login'))
    form = PictureForm()
    title = 'Upload Image'

    if form.validate_on_submit():
        if form.picture.data:
            # Uploading images depends on the machine
            filename = secure_filename(form.picture.data.filename)
            filename_without_extension = (filename.split('.'))[0]
            img_folder_name = str(filename_without_extension+str(int(time.time())))
            username = str(current_user.username)
            cwd = os.getcwd()
            user_image_path = os.path.join(cwd, 'app', 'static', 'images', username) # USER GALLERY FOLDER
            if not os.path.exists(user_image_path):
                os.mkdir(user_image_path)
            picture_path = os.path.join(cwd, 'app', 'static', 'images', username, img_folder_name) # FOLDER for SINGLE IMAGE
            html_path = os.path.join('static', 'images', username, img_folder_name)

            path_dict = {
                'rootdir': picture_path,
                'normal': os.path.join(picture_path, 'normal'),
                'thumbnail': os.path.join(picture_path, 'thumbnail'),
                'blur': os.path.join(picture_path, 'blur'),
                'shade': os.path.join(picture_path, 'shade'),
                'spread': os.path.join(picture_path, 'spread')
            }

            # unsure of this
            # user_email = current_user.email
            # user = User.query.filter_by(email=user_email).first()
            pic_path = ImageLocation(location=picture_path, htmlpath=html_path, filename=filename, user_id=current_user.id)

            # save the image file itself on the local machine
            os.mkdir(picture_path)
            os.mkdir(path_dict['normal'])
            os.mkdir(path_dict['thumbnail'])
            os.mkdir(path_dict['blur'])
            os.mkdir(path_dict['shade'])
            os.mkdir(path_dict['spread'])

            main_path = os.path.join(path_dict['normal'], filename)
            thumbnail_path = os.path.join(path_dict['thumbnail'], filename)
            blur_path = os.path.join(path_dict['blur'], filename)
            shade_path = os.path.join(path_dict['shade'], filename)
            spread_path = os.path.join(path_dict['spread'], filename)

            form.picture.data.save(main_path)
            blur_test = image_transform(main_path, blur_path, 0) # add errors if didn't work
            shade_test = image_transform(main_path, shade_path, 1)
            spread_test = image_transform(main_path, spread_path, 2)
            thumbnail_test = image_transform(main_path, thumbnail_path, 3)

            # add picture path to the database
            db.session.add(pic_path)
            db.session.commit()

    return render_template('upload.html', title=title, form=form)

@app.route('/uploadurl', methods=['GET', 'POST'])
def uploadurl():
    if not current_user.is_authenticated:
        flash('Please login to upload images', category='danger')
        return redirect(url_for('login'))
    form = URLPictureForm()
    title = 'Upload Image via URL'

    if form.validate_on_submit():
        if form.urlpicture.data:
            # Uploading images depends on the machine

            # check file size from URL by checking the header using request library
            # header settings give full uncompressed fizesize
            try:
                r = requests.head(str(form.urlpicture.data),headers={'Accept-Encoding': 'identity'})
                size = int(r.headers['content-length'])
            except:
                flash('Image URL was improperly entered or not a viable image URL, please try another upload', category='danger')
                return redirect(url_for('uploadurl'))
            if size > 10000000:  # larger than 10MB
                flash("File is too large! Please only upload images below 10MB in filesize")
                return redirect(url_for('uploadurl'))

            viable_img = check_img_url(str(form.urlpicture.data))
            viable_img_truth = viable_img[0]
            if not viable_img_truth:
                flash('Image URL was improperly entered or not a viable image URL, please try another upload', category='danger')
                return redirect(url_for('uploadurl'))

            processed_filename = secure_filename(str(form.urlpicture.data)).replace(".", "_").lower()
            filename_ext = extension_dict[viable_img[1]] # png, jpg, or jpeg 
            filename_without_extension = str(processed_filename[-32:]) # just use the last 256 chars of it 
            filename = filename_without_extension + str(filename_ext)

            try: 
                img_data = requests.get(str(form.urlpicture.data)).content
                with open(filename, 'wb') as handler:
                    handler.write(img_data)
            except:
                flash("Error in downloading image from URL. Please try another.", category='danger')
                return redirect(url_for('uploadurl'))
            

            # filename = secure_filename(form.picture.data.filename)
            # filename_without_extension = (filename.split('.'))[0]
            img_folder_name = str(filename_without_extension+str(int(time.time())))
            username = str(current_user.username)
            cwd = os.getcwd()
            user_image_path = os.path.join(cwd, 'app', 'static', 'images', username)
            if not os.path.exists(user_image_path):
                os.mkdir(user_image_path)
            picture_path = os.path.join(cwd, 'app', 'static', 'images', username, img_folder_name)
            html_path = os.path.join('static', 'images', username, img_folder_name)

            path_dict = {
                'rootdir': picture_path,
                'normal': os.path.join(picture_path, 'normal'),
                'thumbnail': os.path.join(picture_path, 'thumbnail'),
                'blur': os.path.join(picture_path, 'blur'),
                'shade': os.path.join(picture_path, 'shade'),
                'spread': os.path.join(picture_path, 'spread')
            }

            # unsure of this
            # user_email = current_user.email
            # user = User.query.filter_by(email=user_email).first()
            pic_path = ImageLocation(location=picture_path, htmlpath=html_path, filename=filename, user_id=current_user.id)

            # save the image file itself on the local machine
            os.mkdir(picture_path)
            os.mkdir(path_dict['normal'])
            os.mkdir(path_dict['thumbnail'])
            os.mkdir(path_dict['blur'])
            os.mkdir(path_dict['shade'])
            os.mkdir(path_dict['spread'])

            # form.picture.data.save(main_path)
            shutil.copy(filename, path_dict['normal'])

            main_path = os.path.join(path_dict['normal'], filename)
            thumbnail_path = os.path.join(path_dict['thumbnail'], filename)
            blur_path = os.path.join(path_dict['blur'], filename)
            shade_path = os.path.join(path_dict['shade'], filename)
            spread_path = os.path.join(path_dict['spread'], filename)

            blur_test = image_transform(main_path, blur_path, 0) # add errors if didn't work
            shade_test = image_transform(main_path, shade_path, 1)
            spread_test = image_transform(main_path, spread_path, 2)
            thumbnail_test = image_transform(main_path, thumbnail_path, 3)

            if blur_test < 0 or shade_test < 0 or spread_test < 0 or thumbnail_test < 0:
                flash('Image could not be transformed! Please try again or another', category='danger')
                return redirect(url_for('uploadurl'))

            # add picture path to the database
            db.session.add(pic_path)
            db.session.commit()

            # remove the temp file
            os.remove(filename)

            flash('Upload successful.')

    return render_template('uploadurl.html', title=title, form=form)


@app.errorhandler(413)
def too_large(e):
    flash("File is too large! Please only upload images below 10MB in filesize")
    return redirect(url_for('upload'))


# gallery will go here 
@app.route('/gallery', methods=['GET'])
def gallery():
    if not current_user.is_authenticated:
        flash('Please login to view your gallery', category='danger')
        return redirect(url_for('login'))
    title = "{}'s Image Gallery".format(str(current_user.username))
    image_path_rows = ImageLocation.query.filter_by(user_id=current_user.id).all()
    # url_friendly_filename = str(img.filename).replace(".", "_")
    image_paths = [{
        'filename': str(img.filename),
        'filename_url': str(str(img.filename).replace(".", "$")),
        'dirname': str(os.path.basename(os.path.normpath(str(img.htmlpath)))),
        'root': str(img.htmlpath),
        'thumbnail': os.path.join(str(img.htmlpath), 'thumbnail', str(img.filename)),
        'normal': os.path.join(str(img.htmlpath), 'normal', str(img.filename)),
        'blur': os.path.join(str(img.htmlpath), 'blur', str(img.filename)),
        'shade': os.path.join(str(img.htmlpath), 'shade', str(img.filename)),
        'spread': os.path.join(str(img.htmlpath), 'spread', str(img.filename))} for img in image_path_rows]
    # image_paths = [{'thumbnail': "/static/images/sample.jpg"}, {'thumbnail': "/static/images/testimg.png"}]
    # flash(str(image_paths))
    return render_template('gallery.html', title=title, image_paths=image_paths)

@app.route('/image/<imagefolder>/<imgname>', methods=['GET'])
def image(imagefolder, imgname):
    if not current_user.is_authenticated:
        flash('Please login to view your gallery', category='danger')
        return redirect(url_for('login'))
    username = str(current_user.username)
    html_path = str(os.path.join('images', username, imagefolder))
    filename = str(imgname).replace("$", ".")
    path_components = {
        'username': username,
        'dirname': imagefolder,
        'filename': filename
    }
    return render_template('image.html', title=imagefolder, pathcomp=path_components)
    # return render_template('image.html', title=imgname, norm=normurl, blur=blururl, shade=shadeurl, spread=spreadurl)