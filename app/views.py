from flask import render_template, flash, redirect, session, url_for, request
from requests.exceptions import HTTPError
from app import app, firebase, db, auth
from .forms import LoginForm, SignupForm
from .decorators import logged_in, not_logged_in
from flask_mail import Mail, Message
from forms import ContactForm

#app.secret_key = 'this will prevent CSRF attacks' #hidden tag?

@app.route('/')
@app.route('/index')
def index():
    user = None
    if 'idToken' in session:
        user = auth.get_account_info(session['idToken'])
        print("Found session for user.")

    return render_template("index.html", title='Home', user=user)


@app.route('/signup', methods=['GET', 'POST'])
@not_logged_in
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = None
        try:
            user = auth.create_user_with_email_and_password(form.email.data, form.password.data)
        except HTTPError: pass

        if user is not None:
            # verify email (form validator is just a regex!)
            auth.send_email_verification(user['idToken'])
            # save details in the user data table
            userdata = { "firstname": form.firstname.data,
                        "lastname": form.lastname.data }
            db.child("users").push(userdata, user['idToken'])

            flash('Thanks for signing up!')
            return redirect(url_for('login'))
        else:
            # TODO this message may not be accurate
            flash('An account already exists for that email address!')
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html', title='Sign up', form=form)


@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # try to authenticate
        user = None
        try:
            user = auth.sign_in_with_email_and_password(form.email.data, form.password.data)
        except HTTPError: pass

        if user is not None:
            # if auth succeeds, see if email is verified
            accountInfo = auth.get_account_info(user['idToken'])

            if (not accountInfo['users'][0]['emailVerified']):
                flash('Please verify your email address!')
                return redirect(url_for('index'))
            else:
                # create new user session
                session['idToken'] = user['idToken']
                flash('Login complete for email="%s"' % (form.email.data))
                return redirect(url_for('index'))
        else:
            flash('Sorry, we couldn\'t find those credentials!')
            return redirect(url_for('login'))
    else:
        return render_template('login.html', title='Sign in', form=form)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
  mail = Mail(app)
  form = ContactForm(request.form)
  if request.method == 'POST':
      if form.validate() == False:
        flash('All fields are required.')
        return render_template('contact.html', form=form)
      else: 
        msg = Message('Coffee@CU Email', sender='coffeeatcu@gmail.com', recipients=['hm2602@barnard.edu'])
        msg.body = """
        New Message from %s %s
        %s
        %s
        """ % ('User firstname', 'User lastname', 'User email', form.message.data)
        mail.send(msg)
        flash('Sent')
        return redirect(url_for('index'))
  elif request.method == 'GET':
      return render_template('contact.html', form=form)

@app.route('/logout')
@logged_in
def logout():
    session.pop('idToken', None) # end user session
    return redirect(url_for('index'))

# ==========================
# ===== error handlers =====
# ==========================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors."""
    return render_template('error/400.html'), 400

@app.errorhandler(401)
def not_authorized(error):
    """Handle 401 errors."""
    return render_template('error/401.html'), 401

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return render_template('error/403.html'), 403

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('error/404.html'), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return render_template('error/405.html', method=request.method), 405

@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    return render_template('error/500.html'), 500
