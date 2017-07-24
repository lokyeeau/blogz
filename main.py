from datetime import datetime
from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'Testing'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(2000))
    post_time = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, post_time=None):
        self.title = title
        self.body = body
        self.owner = owner
        if post_time is None:
            post_time = datetime.utcnow()
        self.post_time = post_time

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120))
    password_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'select_blog', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.password_hash):
            session['username'] = username
            flash("Logged in successfully")
            return redirect('/newpost')
        else:
            existing_user = User.query.filter_by(username=username).first()
            existing_password = User.query.filter_by(password_hash=password).first()
            if username != existing_user:
                login_error = "That username does not exist"
                error = True
            if username == existing_user and password != existing_password:
                login_error = "Password does not match username"
                error = True
            return render_template('login.html', login_error=login_error, error = error)
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = False
    signup_error = ''

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            signup_error = "User already exists"
            error = True
        if len(username) < 3:
            signup_error = "Username must be 3 characters or longer"
            error = True
        if len(password) < 3:
            signup_error = "Password must be 3 characters or longer"
            error = True
        if len(password) < 3 and len(username) < 3:
            signup_error = "Username and Password must be 3 characters or longer"
        if password != verify:
            signup_error = "Passwords do not match"
            error = True

        if error == True:
            return render_template('signup.html', error = error, signup_error = signup_error)

        new_user = User(username, password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect('/newpost')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/blog', methods=['GET', 'POST'])
def blog():
    blogs = request.args.get('id')
    user = request.args.get('username')
    post_time = request.args.get('post_time')

    blogs = Blog.query.all()
    user = User.query.filter_by(username = user).all()
    post_time = Blog.query.order_by(Blog.post_time.desc()).all()

    return render_template('blog.html', blogs=blogs, user=user, post_time=post_time)

@app.route('/newpost', methods=['GET', 'POST'])
def post():
    error = False
    title_error = ''
    body_error = ''

    owner = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        post_title = request.form['post_title']
        post_body = request.form['post_body']

        if len(post_title) < 1:
            title_error = "Give your post a title!"
            error = True

        if len(post_body) < 1:
            body_error = "Your blog needs words...Write something!"
            error = True

        if error == True:
            return render_template('newpost.html', title='Write a new post', error = error, title_error = title_error, body_error = body_error)
    
        new_post = Blog(post_title, post_body, owner)
        db.session.add(new_post)
        db.session.commit()
        post_id = str(new_post.id)
        flash("Success! You published a blog post.")
        return redirect('/select_blog?id=' + post_id)

    return render_template('/newpost.html', title="Write a new post", error=error, title_error=title_error, body_error=body_error, owner=owner)

@app.route('/select_blog', methods=['GET', 'POST'])
def select():
    post_id = request.args.get('id')
    owner = request.args.get('owner_id')
    blog_post = Blog.query.filter_by(id=post_id).first()
    return render_template('select_blog.html', select_blog=blog_post)

if __name__ == "__main__":
    app.run()