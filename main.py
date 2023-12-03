from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import requests
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = 'blog.db'
API_KEY = '545b4cb9483a4dee8f562ae8300d2224'
API_ENDPOINT = f'https://newsapi.org/v2/top-headlines?country=us&category=technology&apiKey={API_KEY}'

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.context_processor
def inject_zip():
    return dict(zip=zip)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_COOKIE_SECURE'] = True # set secure flag
app.config['SESSION_COOKIE_HTTPONLY'] = True  # set httponly flag
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # set samesite flag

@app.after_request
def apply_csp(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src *; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
    return response

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Check if the file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database initialization
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT,
                tags TEXT,
                timestamp TEXT,
                image_filename TEXT
            );
        ''')
        db.commit()


init_db()

# Routes for the application
@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()

    response = requests.get(API_ENDPOINT)
    news_data = response.json()
    articles = news_data.get('articles', [])[:4]  # Limit to 4 articles

    return render_template('index.html', posts=posts, articles=articles)

# Route for the submit page
@app.route('/submit', methods=['POST', 'GET'])
def submit():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form.get('author', 'Anonymous')
        tags = request.form.get('tags', '')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Resize the image using Pillow
                with Image.open(filepath) as img:
                    img = img.resize((300, 200))
                    img.save(filepath)

                image_filename = filename

        if not title or not content:
            flash('Please fill in both fields!')
            return redirect(url_for('submit'))

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO posts (title, content, author, tags, timestamp, image_filename) VALUES (?, ?, ?, ?, ?, ?)',
            (title, content, author, tags, current_time, image_filename))
        db.commit()
        db.close()

        flash('Post submitted successfully!')
        return redirect(url_for('index'))
    return render_template('submit.html')

# Run the application on port 8080
if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0')






