
import os
import secrets
from flask import request, jsonify, render_template, url_for, flash, redirect, abort, session
from Get_Weather import get_response, get_weather_summary, get_temperatures, get_humidity
from WeatherExpress.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                PostForm, RequestResetForm, ResetPasswordForm)
from WeatherExpress.models import User, Post
from WeatherExpress import application, mongo, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required, LoginManager
from flask_mail import Message
from PIL import Image
from pymongo.errors import OperationFailure
from math import ceil
from bson import ObjectId
import sys
sys.path.append('./protobuf')
from protobuf import grpc_client, weather_pb2_grpc, weather_pb2
import openai
import json
import client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protobuf')))

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()
    print("Whoever's looking at this is stupid haha")


posts = [
    {
        'author': 'Corey Schafer',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]



@application.route("/")
@application.route("/home")
def home():
    api_key = os.environ.get('GOOGLE_API_KEY')
    print(api_key)
    return render_template('home.html', posts=posts, api_key=api_key)

def get_user_image_file(user_id):
    """Get Image file associated with user_id"""
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        return user['image_file']
    return None

def get_username(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        return user['username']
    return None


@application.route("/blog")
def blog():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    # Retrieve total count of documents in the 'posts' collection
    total_posts = mongo.db.posts.count_documents({})
    # Calculate the skip value based on the current page and per_page value
    skip = (page - 1) * per_page
    cursor = mongo.db.posts.find().sort('date_posted', -1).skip(skip).limit(per_page)
    # Retrieve posts from MongoDB using the 'find' method with query operators
    posts = list(cursor)
    # Calculate total pages for pagination
    total_pages = ceil(total_posts / per_page)
    user_list = []
    for post in posts:
        # Check if '_id' key is present and is of type ObjectId
        if '_id' in post and isinstance(post['_id'], ObjectId):
            # Convert ObjectId to string
            post['_id'] = str(post['_id'])
        user_list.append(get_user_image_file(post['user_id']))
    return render_template('blog.html', posts=posts, total_posts=total_posts, page=page, per_page=per_page, num_posts=len(posts), total_pages=total_pages, user_list=user_list, count=0)


@application.route("/about")
def about():
    return render_template('about.html', title='About')


@application.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        user.save()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@application.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        
        return redirect(url_for('home'))
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user_data = mongo.db.users.find_one({'email': email})

        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            # Check if 'image_file' key is present in user_data
            
            if 'image_file' in user_data:
                user = User(
                            username=user_data['username'], 
                            email=user_data['email'],
                            password=user_data['password'], 
                            image_file=user_data['image_file'],
                            id=user_data['_id'])
            else:
                user = User(username=user_data['username'], 
                            email=user_data['email'], 
                            password=user_data['password'], 
                            id=user_data['_id']) # Use default image_file
           
            login_user(user, remember=form.remember.data)
         
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@application.route('/get_weather', methods=['GET'])
def weather():
    return client.get_weather(request.args.get('city'), request.args.get('unit', 'C'))

@application.route('/weather_gpt', methods=['GET'])
def weather_gpt():
    return render_template('weather_gpt.html')
    
@application.route('/weather_chat', methods=['POST'])
def weather_chat():
    openai.api_key = os.environ.get('OPEN_API_KEY')
    model_engine = 'text-davinci-002'
    user_input = request.json['message']
    weather_response = client.get_weather(user_input, 'C')
    
    if isinstance(weather_response, tuple) and weather_response[1] != 200:
        return {'message': "Invalid message, retry again"}
    weather_dict = json.loads(weather_response[0])

    high_temp_am = weather_dict['high_temp_am']
    high_temp_night = weather_dict['high_temp_night']
    high_temp_pm = weather_dict['high_temp_pm']
    humidity_am = weather_dict['humidity_am']
    humidity_night = weather_dict['humidity_night']
    humidity_pm = weather_dict['humidity_pm']
    low_temp_am = weather_dict['low_temp_am']
    low_temp_night = weather_dict['low_temp_night']
    low_temp_pm = weather_dict['low_temp_pm']
    weather_description = weather_dict['weather_description']
    weather_summary = weather_dict['weather_summary']


    prompt = f"Describe what the weather is like in {user_input}. "
    prompt += f"It is {weather_summary} with a high of {high_temp_pm}°C in the afternoon, {high_temp_am}°C in the morning, and {high_temp_night}°C at night. "
    prompt += f"The low temperature ranges from {low_temp_am}°C in the morning, {low_temp_pm}°C in the afternoon, to {low_temp_night}°C at night. "
    prompt += f"The humidity is {humidity_pm}% in the afternoon, {humidity_am}% in the morning, and {humidity_night}% at night. "
    prompt += f"{weather_description}"
    prompt += "What type of clothing would you recommend for this weather? Should I bring an umbrella? Please provide detailed information about the exact temperature and humidity."
    prompt += f"Also, could you suggest some fun things to do around {user_input}? Please describe in detail."


    response = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.7
    )
    bot_response = response.choices[0].text

    return {'message': bot_response}

@application.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(application.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@application.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.save()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.get_username()
        form.email.data = current_user.get_email()
    
    image_file = url_for('static', filename='profile_pics/' + current_user.get_image_file())
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@application.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.get_id(),
        )
        post_dict = post.to_dict()
        mongo.db.posts.insert_one(post_dict)
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@application.route("/post/<string:post_id>")
@login_required
def post(post_id):
    # Query the 'posts' collection in MongoDB by '_id'
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    image_file = get_user_image_file(post['user_id'])
    username = get_username(post['user_id'])
    str_post_id = str(post['_id'])

    if post:
        return render_template('post.html', title=post['title'], post=post, image_file=image_file, username=username, str_post_id=str_post_id )
    else:
        # Return a custom 404 error page if post not found
        return render_template('404.html'), 404

@application.route("/post/<string:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if post is None:
        render_template('404.html'), 404
    if get_username(post['user_id']) != current_user.get_username():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        mongo.db.posts.update_one({'_id': ObjectId(post_id)},
                                  {'$set': {'title': form.title.data, 'content': form.content.data}})
        post['title'] = form.title.data
        post['content'] = form.content.data
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.title.data = post['title']
        form.content.data = post['content']
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@application.route("/post/<string:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        # If post is not found, raise a 404 error
        render_template('404.html'), 404
    # Verify if the post author is the current user
    if get_username(post['user_id']) != current_user.get_username():
        # If post author does not match current user, raise a 403 error
        abort(403)
    try:
        # Delete the post from MongoDB
        mongo.db.posts.delete_one({'_id': ObjectId(post_id)})
        flash('Your post has been deleted!', 'success')
        return redirect(url_for('home'))
    except OperationFailure as e:
        # Handle any errors that may occur during the delete operation
        # For example, if the user does not have the necessary permissions
        print(f'Failed to delete post: {e}')
        abort(500)
    return redirect(url_for('home'))


@application.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    per_page = 5
    skip = (page - 1) * per_page
    user_data = mongo.db.users.find_one({'username': username})  # Retrieve user data from MongoDB
    if not user_data:
        render_template('404.html'), 404  # Raise a 404 error if user not found
    user = User(username=user_data['username'], email=user_data['email'], password=user_data['password'])
    # Retrieve posts from MongoDB using author field and order by date_posted in descending order
    posts = mongo.db.posts.find({'author': user.get_username()}).sort('date_posted', -1).skip(skip).limit(per_page)
    posts = list(posts)
    total_pages = ceil(total_posts / per_page)
    user_list = []
    for post in posts:
        if '_id' in post and isinstance(post['_id'], ObjectId):
            # Convert ObjectId to string
            post['_id'] = str(post['_id'])
        user_list.append(get_user_image_file(post['user_id']))
    # Count total number of posts for pagination
    total_posts = mongo.db.posts.count_documents({'author': user.get_username})
    return render_template('user_posts.html', posts=posts, total_posts=total_posts, page=page, per_page=per_page, num_posts=len(posts), total_pages=total_pages, user_list=user_list, count=0)
    


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@WeatherExpress.com',
                  recipients=[user.get_email()])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}
If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@application.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user_data = mongo.db.users.find_one({'email': form.email.data})
        if user_data is None:
            render_template('404.html'), 404
        else:
            user = User(
                        username=user_data['username'], 
                        email=user_data['email'],
                        password=user_data['password'], 
                        image_file=user_data['image_file'],
                        id=user_data['_id'])
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@application.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    user = mongo.db.users.find_one({'reset_token': token})
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        try:
            mongo.db.users.update_one({'reset_token': token}, {'$set': {'password': hashed_password}})
            flash('Your password has been updated! You are now able to log in', 'success')
            return redirect(url_for('login'))
        
        except OperationFailure as e:
            # Handle any errors that may occur during the update operation
            # For example, if the user does not have the necessary permissions
            print(f'Failed to update password: {e}')
            abort(500)
            return redirect(url_for('login'))
        
    return render_template('reset_token.html', title='Reset Password', form=form)


# Custom error handler for 404 errors
@application.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404