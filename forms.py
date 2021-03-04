from flask_ckeditor import CKEditor, CKEditorField
from wtforms import StringField, TextAreaField, validators
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


# FORMS:
###############################
# Post form
class AddNewPost(FlaskForm):
    title = StringField('Title', [DataRequired()])
    body = CKEditorField('Blog Content', [DataRequired()])
    author = TextAreaField('Your Name', [DataRequired()])
    img_url = TextAreaField('Image Url', [DataRequired()])
    subtitle = TextAreaField('Subtitle', [DataRequired()])


# Contact form
class ContactForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25), DataRequired()])
    email = StringField('Email Address', [validators.Length(min=6, max=35), DataRequired()])
    phone = StringField('Phone Number', [validators.Length(min=6, max=35), DataRequired()])
    message = TextAreaField('Message', [validators.Length(min=6, max=55), DataRequired()])


# Register form
class RegisterForm(FlaskForm):
    name = StringField('Name', [validators.Length(min=4, max=25), DataRequired()])
    email = StringField('Email', [DataRequired()])
    password = StringField('Password', [validators.Length(min=6, max=35), DataRequired()])


# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', [DataRequired()])
    password = StringField('Password', [validators.Length(min=6, max=35), DataRequired()])

# Comment form
class CommentForm(FlaskForm):
    comment = CKEditorField('Comment', [DataRequired()])

###############################