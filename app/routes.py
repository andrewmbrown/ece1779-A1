import os
import time
import requests
import urllib.request
import shutil
import json
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
from datetime import datetime
# from apscheduler.schedulers.background import BackgroundScheduler  # for posting http req data

from access import access_keys

import boto3 #a3 onward!! 
#import s3 stuff into here

'''
# This code is the driver/state of the app
# each function defines the behaviour of a certain part of the app
# performs logical functions then renders html display 
@app.route('/')  # decorator, modifies the function that follows it
'''

AWS_ACC_KEY = access_keys["AWS_ACC_KEY"]
AWS_SEC_KEY = access_keys["AWS_SECRET_KEY"]

s3_client = boto3.client('s3', 
    aws_access_key_id=AWS_ACC_KEY, 
    aws_secret_access_key=AWS_SEC_KEY, 
    region_name="us-east-1")
cloudwatch = boto3.client('cloudwatch',
        aws_access_key_id=AWS_ACC_KEY, 
        aws_secret_access_key=AWS_SEC_KEY, 
        region_name="us-east-1")
ec2 = boto3.client('ec2',
        aws_access_key_id=AWS_ACC_KEY, 
        aws_secret_access_key=AWS_SEC_KEY, 
        region_name="us-east-1")
count = 0  # cloudwatch and count to publish http_req to be displayed on manager app
bucket = 'ece1779a3g81'
bucket_url_base = 'https://ece1779a3g81.s3.amazonaws.com/'

rds_db_base = 'test'

# Defining a before_request to increment count each time we see a request
@app.before_request
def before_request():
    global count
    count += 1
    return

'''
# APScheduler that pushes the HTTP request count to cloudwatch every minute, and resets count
def publish_metrics():
    global count
    try:
        # ip address gives the meta-data for the current ec2 machine
        # this is assumed this code is built ON the ec2, if not its a local machine
        response = requests.get('http://169.254.169.254/latest/meta-data/instance-id')
        instance_id = response.text
    except:
        instance_id = 'localhost'

    ## API to publish metrics
    response = cloudwatch.put_metric_data(
        Namespace='HTTP_Requests',
        MetricData=[
            {
                'MetricName': 'HTTP_Requests',
                'Dimensions':[
                    {
                    'Name': 'Instance_ID',
                    'Value': instance_id
                    },
                ],
                'Timestamp': datetime.utcnow(),
                'Unit': 'None',
                'Value': count
            },
        ]   
    )
    print('Pushing metrics now. Count and response: ', count, instance_id, response)
    count = 0
    
scheduler = BackgroundScheduler()
job = scheduler.add_job(publish_metrics, 'interval', minutes=1)
scheduler.start()
'''

# To ensure we always have an admin account we attempt to make it every time
# in case there are no accounts
# email must be setup with a gmail that has proper permissions (passwords) and for emailing using 3rd party code
def setup():
    # function to attempt to create admin account every time the webapp is started
    # since at least one account needs administrator priveleges, it needs to exist
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = ''  # set this yourself, needs to be a gmail with permissions
    app.config['MAIL_PASSWORD'] = ''  # set this yourself
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # <10MB server side validation
    mail = Mail(app)
    try:
        admin = User(username='root', email='root@email.com')
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        print("added admin, username: root, password: password")
    except:
        print("Admin user account already exists")
    return mail

mail = setup()  # configure admin account and setup mail
@app.route('/')
@app.route('/index')  # use as register fxn as callbacks for certain events
@login_required
def index():
    # render_template() invokes jinja2 substituting {{...}} blocks with corresponding values
    admin_info = [
        {
            'author': {'username': 'Admin (root) says:'},
            'body': 'Please use the Navigation Bar above to utilize this web application'
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

# Method to logout authenticated user
@app.route('/logout')
def logout():
    logout_user()
    flash("Successfully logged out")
    return redirect(url_for('index'))

# method to register user who has administrator priveleges
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

        # as a form of password recovery, send email containing it - THIS NEEDS CONFIGURING IF YOU USE IT IN PRODUCTION
        try:
            msg = Message('Account Details', sender = 'andrewm.brown@mail.utoronto.ca', recipients = [form.email.data])
            msg.body = f"Hello, {form.username.data}, here is your password in case you lose it: {form.password.data} You can also reset this password via the application"
            mail.send(msg)
            flash("Sent account details (username, passsword) to your email!")
        except:
            flash("Unable to send account details to email to your email!")
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# Recover method functions both as password reset and password change for users
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

# Upload method for users 
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
            html_path_old = os.path.join('static', 'images', username, img_folder_name)
            http_path = bucket_url_base + "static/images/" + username + "/" + img_folder_name + "/"
            s3_path = "/".join(['static','images', username, img_folder_name])

            path_dict = {
                'rootdir': picture_path,
                'normal': os.path.join(picture_path, 'normal'),
                'thumbnail': os.path.join(picture_path, 'thumbnail'),
                'blur': os.path.join(picture_path, 'blur'),
                'shade': os.path.join(picture_path, 'shade'),
                'spread': os.path.join(picture_path, 'spread')
            }

            s3_dict = {
                'rootdir': s3_path,
                'normal': "/".join([s3_path, 'normal']),
                'thumbnail': "/".join([s3_path, 'thumbnail']),
                'blur': "/".join([s3_path, 'blur']),
                'shade': "/".join([s3_path, 'shade']),
                'spread': "/".join([s3_path, 'spread'])
            }

            
            # pic_path = ImageLocation(location=picture_path, htmlpath=html_path, filename=filename, user_id=current_user.id)
            pic_path = ImageLocation(location=picture_path, httppath=http_path, s3path=s3_path, filename=filename, user_id=current_user.id)

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

            main_path_s3 = "/".join([s3_dict['normal'], filename])
            thumbnail_path_s3 = "/".join([s3_dict['thumbnail'], filename])
            blur_path_s3 = "/".join([s3_dict['blur'], filename])
            shade_path_s3 = "/".join([s3_dict['shade'], filename])
            spread_path_s3 = "/".join([s3_dict['spread'], filename])

            form.picture.data.save(main_path)
            blur_test = image_transform(main_path, blur_path, 0) # add errors if didn't work
            shade_test = image_transform(main_path, shade_path, 1)
            spread_test = image_transform(main_path, spread_path, 2)
            thumbnail_test = image_transform(main_path, thumbnail_path, 3)

            s3_client.upload_file(main_path, bucket, main_path_s3)
            s3_client.upload_file(blur_path, bucket, blur_path_s3)
            s3_client.upload_file(shade_path, bucket, shade_path_s3)
            s3_client.upload_file(spread_path, bucket, spread_path_s3)
            s3_client.upload_file(thumbnail_path, bucket, thumbnail_path_s3)

            shutil.rmtree(user_image_path)

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
            if size > 10000000:  # larger than 10MB, server side check
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
            

            img_folder_name = str(filename_without_extension+str(int(time.time())))
            username = str(current_user.username)
            cwd = os.getcwd()
            user_image_path = os.path.join(cwd, 'app', 'static', 'images', username)
            if not os.path.exists(user_image_path):
                os.mkdir(user_image_path)
            picture_path = os.path.join(cwd, 'app', 'static', 'images', username, img_folder_name)
            html_path = os.path.join('static', 'images', username, img_folder_name)
            html_path_old = os.path.join('static', 'images', username, img_folder_name)
            http_path = bucket_url_base + "static/images/" + username + "/" + img_folder_name + "/"
            s3_path = "/".join(['static','images', username, img_folder_name])

            path_dict = {
                'rootdir': picture_path,
                'normal': os.path.join(picture_path, 'normal'),
                'thumbnail': os.path.join(picture_path, 'thumbnail'),
                'blur': os.path.join(picture_path, 'blur'),
                'shade': os.path.join(picture_path, 'shade'),
                'spread': os.path.join(picture_path, 'spread')
            }

            s3_dict = {
                'rootdir': s3_path,
                'normal': "/".join([s3_path, 'normal']),
                'thumbnail': "/".join([s3_path, 'thumbnail']),
                'blur': "/".join([s3_path, 'blur']),
                'shade': "/".join([s3_path, 'shade']),
                'spread': "/".join([s3_path, 'spread'])
            }
        
            # pic_path = ImageLocation(location=picture_path, httppath=html_path, s3path=s3_path, filename=filename, user_id=current_user.id)
            pic_path = ImageLocation(location=picture_path, httppath=http_path, s3path=s3_path, filename=filename, user_id=current_user.id)

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

            main_path_s3 = "/".join([s3_dict['normal'], filename])
            thumbnail_path_s3 = "/".join([s3_dict['thumbnail'], filename])
            blur_path_s3 = "/".join([s3_dict['blur'], filename])
            shade_path_s3 = "/".join([s3_dict['shade'], filename])
            spread_path_s3 = "/".join([s3_dict['spread'], filename])

            blur_test = image_transform(main_path, blur_path, 0) # add errors if didn't work
            shade_test = image_transform(main_path, shade_path, 1)
            spread_test = image_transform(main_path, spread_path, 2)
            thumbnail_test = image_transform(main_path, thumbnail_path, 3)

            if blur_test < 0 or shade_test < 0 or spread_test < 0 or thumbnail_test < 0:
                flash('Image could not be transformed! Please try again or another', category='danger')
                return redirect(url_for('uploadurl'))

            s3_client.upload_file(main_path, bucket, main_path_s3)
            s3_client.upload_file(blur_path, bucket, blur_path_s3)
            s3_client.upload_file(shade_path, bucket, shade_path_s3)
            s3_client.upload_file(spread_path, bucket, spread_path_s3)
            s3_client.upload_file(thumbnail_path, bucket, thumbnail_path_s3)

            # add picture path to the database
            db.session.add(pic_path)
            db.session.commit()

            # remove the temp file
            os.remove(filename)
            shutil.rmtree(user_image_path)

            flash('Upload successful.')

    return render_template('uploadurl.html', title=title, form=form)


# gallery will go here 
@app.route('/gallery', methods=['GET'])
def gallery():
    if not current_user.is_authenticated:
        flash('Please login to view your gallery', category='danger')
        return redirect(url_for('login'))
    title = "{}'s Image Gallery".format(str(current_user.username))
    image_path_rows = ImageLocation.query.filter_by(user_id=current_user.id).all()
    # url_friendly_filename = str(img.filename).replace(".", "_")
    '''
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
    '''
    image_paths = [{
        'filename': str(img.filename),
        'filename_url': str(str(img.filename).replace(".", "$")),
        'dirname': str(os.path.basename(os.path.normpath(str(img.s3path)))),
        'root': str(img.s3path),
        'thumbnail': str(str(img.httppath) + "thumbnail/" + str(img.filename))
    } for img in image_path_rows]
    # image_paths = [{'thumbnail': "/static/images/sample.jpg"}, {'thumbnail': "/static/images/testimg.png"}]
    # flash(str(image_paths))
    # print("image paths")
    # print(image_paths)
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
        'filename': filename,
        'normal': bucket_url_base+'static/images/'+username+"/"+imagefolder+"/normal/"+filename,
        'blur': bucket_url_base+'static/images/'+username+"/"+imagefolder+"/blur/"+filename,
        'shade': bucket_url_base+'static/images/'+username+"/"+imagefolder+"/shade/"+filename,
        'spread': bucket_url_base+'static/images/'+username+"/"+imagefolder+"/spread/"+filename
    }
    # print(path_components)
    return render_template('image.html', title=imagefolder, pathcomp=path_components)

# Automatic testing points
@app.route('/api/register', methods=['POST'])
def register_test():
    # define json success and error codes
    msg_failure = {
        'success': False,
        'error': 
            {'code': 400, 'message': 'Unsuccessful registering'}
    }
    msg_success = {'success': True}

    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = 'default@gmail.com'  # a sample placeholder
        else:
            msg_failure['error']['message'] = 'Request method was specified incorrectly'
            return json.dumps(msg_failure)
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except:
            msg_failure['error']['message'] = 'request data does not conform to proper specifications'
            return json.dumps(msg_failure)
    except:
        msg_failure['error']['message'] = 'Not a POST request or not able to parse data'
        return json.dumps(msg_failure)
    # end of function if all is successful
    return json.dumps(msg_success)

@app.route('/api/upload', methods=['POST'])
def upload_test():
    sample_size = None
    # define json success and error codes
    msg_failure = {
        'success': False,
        'error': 
            {'code': 400,
             'message': 'Unsuccessful registering'}
    }
    msg_success = {
        'success': True,
        'payload': 
            {'original_size': sample_size, 
            'blur_size': sample_size,
            'shade_size': sample_size,
            'spread_size': sample_size}
    }
    try:
        if request.method == 'POST':
            # login with this info
            username = request.form['username']
            password = request.form['password']
        else:
            msg_failure['error']['message'] = 'Request method was specified incorrectly, unable to parse'
            return json.dumps(msg_failure)
        try: # login and upload
            user = User.query.filter_by(username=username).first()  # query for the username
            if user is None or not user.check_password(password): # check user with password validity
                msg_failure['error']['message'] = 'invalid username or password'
                return json.dumps(msg_failure)
            # now we can login user
            login_user(user)
            
            # get file from form filler
            file = request.files['file']
            if not file:
                msg_failure['error']['message'] = 'file is invalid'
                return json.dumps(msg_failure)
            filename = secure_filename(file.filename)
            filename_without_extension = (filename.split('.'))[0]
            img_folder_name = str(filename_without_extension+str(int(time.time())))
            username = str(current_user.username)
            cwd = os.getcwd()
            user_image_path = os.path.join(cwd, 'app', 'static', 'images', username) # USER GALLERY FOLDER
            if not os.path.exists(user_image_path):
                os.mkdir(user_image_path)
            picture_path = os.path.join(cwd, 'app', 'static', 'images', username, img_folder_name)
            html_path = os.path.join('static', 'images', username, img_folder_name)
            html_path_old = os.path.join('static', 'images', username, img_folder_name)
            http_path = bucket_url_base + "static/images/" + username + "/" + img_folder_name + "/"
            s3_path = "/".join(['static','images', username, img_folder_name])

            path_dict = {
                'rootdir': picture_path,
                'normal': os.path.join(picture_path, 'normal'),
                'thumbnail': os.path.join(picture_path, 'thumbnail'),
                'blur': os.path.join(picture_path, 'blur'),
                'shade': os.path.join(picture_path, 'shade'),
                'spread': os.path.join(picture_path, 'spread')
            }

            s3_dict = {
                'rootdir': s3_path,
                'normal': "/".join([s3_path, 'normal']),
                'thumbnail': "/".join([s3_path, 'thumbnail']),
                'blur': "/".join([s3_path, 'blur']),
                'shade': "/".join([s3_path, 'shade']),
                'spread': "/".join([s3_path, 'spread'])
            }
        
            # pic_path = ImageLocation(location=picture_path, httppath=html_path, s3path=s3_path, filename=filename, user_id=current_user.id)
            pic_path = ImageLocation(location=picture_path, httppath=http_path, s3path=s3_path, filename=filename, user_id=current_user.id)

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

            main_path_s3 = "/".join([s3_dict['normal'], filename])
            thumbnail_path_s3 = "/".join([s3_dict['thumbnail'], filename])
            blur_path_s3 = "/".join([s3_dict['blur'], filename])
            shade_path_s3 = "/".join([s3_dict['shade'], filename])
            spread_path_s3 = "/".join([s3_dict['spread'], filename])

            blur_test = image_transform(main_path, blur_path, 0) # add errors if didn't work
            shade_test = image_transform(main_path, shade_path, 1)
            spread_test = image_transform(main_path, spread_path, 2)
            thumbnail_test = image_transform(main_path, thumbnail_path, 3)


            if blur_test < 0 or shade_test < 0 or spread_test < 0 or thumbnail_test < 0:
                msg_failure['error']['message'] = 'Image could not be transformed! Please try again or another'
                return json.dumps(msg_failure)
            else:
                # prepare success message with payload sizes
                msg_success['payload']['original_size'] = os.path.getsize(main_path)
                msg_success['payload']['blur_size'] = os.path.getsize(blur_path)
                msg_success['payload']['shade_size'] = os.path.getsize(shade_path)
                msg_success['payload']['spread_size'] = os.path.getsize(spread_path)

            s3_client.upload_file(main_path, bucket, main_path_s3)
            s3_client.upload_file(blur_path, bucket, blur_path_s3)
            s3_client.upload_file(shade_path, bucket, shade_path_s3)
            s3_client.upload_file(spread_path, bucket, spread_path_s3)
            s3_client.upload_file(thumbnail_path, bucket, thumbnail_path_s3)

            # add picture path to the database
            db.session.add(pic_path)
            db.session.commit()

            # remove the temp file
            os.remove(filename)
            shutil.rmtree(user_image_path)

        except:
            msg_failure['error']['message'] = 'unable to upload file'
            return json.dumps(msg_failure)
    except:
        msg_failure['error']['message'] = 'Not a POST request or not able to parse data'
        return json.dumps(msg_failure)

    # end of function if all is successful
    return json.dumps(msg_success)

# Various error handling functions, each serving an individual purpose
# handle error if file is too large, redirect to uplod
@app.errorhandler(413)
def too_large(e):
    flash("File is too large! Please only upload images below 10MB in filesize")
    return redirect(url_for('upload'))

# handle if file not found error, 404
@app.errorhandler(404)
def not_found_error(e):
    return render_template('404.html'), 404

# handle error if there is any database error, rollback db
@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500
