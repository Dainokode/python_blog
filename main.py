from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from forms import ContactForm, RegisterForm, LoginForm, AddNewPost, CommentForm
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from datetime import datetime
from flask_gravatar import Gravatar
from dotenv import load_dotenv
import smtplib
import os


# load .env file
load_dotenv('.env')


# App configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'some key'
file_path = os.path.abspath(os.getcwd())+"\\blog.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
ckeditor = CKEditor(app)
Base = declarative_base()


# Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# DB MODELS:
##############################
class User(UserMixin, db.Model, Base):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")
    

    def __repr__(self):
        return f"Name: {self.name} - Email: {self.email}"


# Blog model
class Post(db.Model, Base):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    date = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    img_url = db.Column(db.String(280), nullable=False)
    subtitle = db.Column(db.String(120), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")

    def __repr__(self):
        return f"Title: {self.title} - Date: {self.date} - Body: {self.body} - Author: {self.author} - Image Url: {self.img_url} - Subtitle: {self.subtitle}"


class Comment(db.Model, Base):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(280), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_post = relationship("Post", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    comment_author = relationship("User", back_populates="comments")


# db.create_all()
##############################


# login manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user:
        return user
    return None


# Admin decorator
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return render_template("403.html"), 403
        except:
            return render_template("403.html"), 403
        return func(*args, **kwargs)
    return decorated_function


# Blog posts
@app.route('/')
def home():
    blog_data = Post.query.all()
    year = datetime.now().year
    return render_template("index.html", year=year, blog_data=blog_data, current_user=current_user)


@app.route('/contact')
def contact():
    form = ContactForm()
    return render_template("contact.html", form=form, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            new_user = User(
                name=request.form["name"],
                email=request.form["email"],
                password=generate_password_hash(request.form["password"], method='pbkdf2:sha256', salt_length=8),
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Successfully registered!")
            login_user(new_user)
            return redirect(url_for("home", current_user=current_user))
        else:
            flash("You already registered this email, try login instead.")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Successfully logged in!")
            return redirect(url_for("home", current_user=current_user))
        elif not user:
            flash("The email doesn not exist. Please try again.")
            return render_template("login.html", form=form)
        elif check_password_hash(user.password, password) == False:
            flash("The password is not correct. Please try again.")
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash("Successfully logged out!")
    return redirect(url_for("home"))



@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    form = CommentForm()
    requested_post = Post.query.get(post_id)
    if request.method == "POST":
        if current_user.is_authenticated:
            new_comment = Comment(
                comment=request.form["comment"],
                comment_author=current_user,
                parent_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            form.comment.data = ""
        else:
            flash("You need to be logged in to comment.")
            return redirect(url_for("login"))
    comments = Comment.query.all()
    return render_template("post.html", article=requested_post, current_user=current_user, form=form, comments=comments)
    


@app.route('/contact', methods=['GET', 'POST'])
def receive_data():
    form = ContactForm()
    my_email = os.environ.get("MY_EMAIL")
    password = os.environ.get("MY_EMAIL_PASSWORD")
    receiver = os.environ.get("RECEIVER_EMAIL")
    success_message = "Your message was successfully sent"
    sender_username = request.form["username"]
    sender_email = request.form["email"]
    sender_phone = request.form["phone"]
    sender_message = request.form["message"]
    message = f'Name {sender_username}\nEmail: {sender_email}\nPhone {sender_phone}\nMessage: {sender_message}'
    if form.validate_on_submit():
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls()
            connection.login(user=my_email, password=password)
            fmt = 'From: {}\r\nTo: {}\r\nSubject: {}\r\n{}'
            connection.sendmail(
                my_email,
                receiver,
                fmt.format(my_email, receiver, "New message", message).encode('utf-8')
            )
            # clear inputs
            form.username.data = ""
            form.email.data = ""
            form.phone.data = ""
            form.message.data = ""
        return render_template("contact.html", form=form, success_message=success_message)
    return render_template("contact.html", form=form)


@app.route('/new-post', methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = AddNewPost()
    if form.validate_on_submit():
        new_post = Post(
            title=request.form["title"],
            date=datetime.now().strftime("%B %d, %Y"),
            body=request.form["body"],
            author=current_user,
            img_url=request.form["img_url"],
            subtitle=request.form["subtitle"],
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("new-post.html", form=form, current_user=current_user)


@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    post = Post.query.get(post_id)
    edit_form = AddNewPost(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data  
        db.session.commit()
        return redirect(url_for("post", post_id=post.id))
    return render_template("new-post.html", form=edit_form, is_edit=True, post_id=post.id, current_user=current_user)



@app.route('/delete-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def delete_post(post_id):
    post = Post.query.get(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)