from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from os.path import join, dirname, realpath, exists
import webbrowser
from flask_ngrok import run_with_ngrok



app = Flask(__name__)

app.config['SECRET_KEY'] = 'corizo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLite database file
db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    content = db.Column(db.String, nullable=False)
    likes = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
UPLOAD_FOLDER = 'uploads'  # Create a folder named 'uploads' in your project directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def upload_post_file(file):
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return file_path
    return None

@app.route('/')
def home():
    return render_template('indexweb.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username, password=password).first()

    if user:
        session['user_id'] = user.id  # Store user_id in session
        return redirect(url_for('index'))
    else:
        flash('Login failed. Please check your username and password.', 'error')

    return redirect(url_for('home'))

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        flash('Username already exists. Please choose a different username.', 'error')
    else:
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful', 'success')

    return redirect(url_for('home'))

@app.route('/index')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        posts = Post.query.filter_by(user_id=user_id).all()
        return render_template('indexweb.html', user=user, posts=posts)
    else:
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('home'))

STATIC_FOLDER = 'static'

@app.route('/upload_post', methods=['POST'])

def upload_post():
    if 'user_id' in session:
        user_id = session['user_id']
        post_type = request.form['post_type']

        if post_type == 'photo':
            content = upload_photo(request.files['content'])
        elif post_type == 'video':
            content = upload_video(request.files['content'])
            
        if content is not None:     
            post = Post(type=post_type, content=content, user_id=user_id)
            db.session.add(post)  # Corrected from new_post to post
            db.session.commit()

        return redirect(url_for('index'))
    else:
        return redirect(url_for('home'))


def upload_photo(file):
    uploads_dir = join(dirname(realpath(__file__)), 'static', 'photos')

    if not exists(uploads_dir):
        os.makedirs(uploads_dir)

    file_path = join(uploads_dir, file.filename)
    file.save(file_path)
    return file_path

def upload_video(file):
    uploads_dir = join(dirname(realpath(__file__)), 'static', 'videos')
    
    if not exists(uploads_dir):
        os.makedirs(uploads_dir)

    file_path = join(uploads_dir, file.filename)
    file.save(file_path)
    return file_path


@app.route('/like/<int:post_id>', methods=['GET', 'POST'])
def like(post_id):
    if 'user_id' in session and request.method == 'POST':
        post = Post.query.get(post_id)
        post.likes += 1
        db.session.commit()
        return redirect(url_for('index'))
    else:
        flash('Please log in to like posts.', 'error')
        return redirect(url_for('home'))

@app.route('/unlike/<int:post_id>', methods=['POST'])
def unlike(post_id):
    if 'user_id' in session:
        post = Post.query.get(post_id)
        post.likes -= 1
        db.session.commit()
        return redirect(url_for('index'))
    else:
        flash('Please log in to unlike posts.', 'error')
        return redirect(url_for('home'))

# Implement the share route
@app.route('/share/<int:post_id>', methods=['POST'])
def share(post_id):
    if 'user_id' in session:
        # Implement sharing logic here
        flash('Post shared successfully!', 'success')
        return redirect(url_for('index'))
    else:
        flash('Please log in to share posts.', 'error')
        return redirect(url_for('home'))


app.static_folder = 'static'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run()
