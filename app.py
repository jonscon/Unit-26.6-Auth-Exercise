from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///users"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)
app.app_context().push()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def home_page():
    """Automatically redirects user to register."""

    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    """Register on this page."""

    form = RegisterForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        new_user = User.register(first_name, last_name, email, username, password)
        
        db.session.add(new_user)
        # If username already exists, show error message
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another.')
            return render_template('register.html', form=form)
        
        session['username'] = new_user.username
        flash('Welcome! Successfully created your account!', "success")
        return redirect(f'/users/{username}')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():
    """Login on this page."""

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['username'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """Logout user."""

    session.pop('username')
    flash("Goodbye!")
    return redirect('/login')


@app.route('/users/<username>', methods=['GET', 'POST'])
def user_info(username):
    """User information."""

    # Only allows logged-in user to access this page
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get_or_404(username)
    return render_template('user.html', user=user)

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    """Form to add feedback."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(title=title, content=content, username=username)

        db.session.add(new_feedback)
        db.session.commit()

        flash("Feedback Created!", "success")
        return redirect(f'/users/{username}')
    
    return render_template('add_feedback.html', form=form)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Delete user and any feedback associated."""

    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get_or_404(username)
    db.session.delete(user)
    db.session.commit()
    session.pop('username')
    
    flash(f"{username} deleted.", "danger")
    return redirect('/')
    
@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback(id):
    """Update feedback."""
    
    feedback = Feedback.query.get_or_404(id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()
    
    form = FeedbackForm()

    # POST route: Update feedback title and content
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.add(feedback)
        db.session.commit()

        flash("Feedback has been updated!", "success")
        return redirect(f'/users/{feedback.username}')

    # GET route: Pre-populate fields with existing values
    form.title.data = feedback.title
    form.content.data = feedback.content
    return render_template("update_feedback.html", form=form)

@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    """Delete feedback."""

    feedback = Feedback.query.get_or_404(id)
    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()
    
    db.session.delete(feedback)
    db.session.commit()
    
    flash("Feedback deleted!", "info")
    return redirect(f'/users/{feedback.username}')

