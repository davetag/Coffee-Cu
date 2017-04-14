from flask import render_template, flash, redirect, session, url_for, request
from app import app, firebase, db, auth, mail
from requests.exceptions import HTTPError
from .forms import LoginForm, SignupForm, ProfileForm, ResetPasswordForm, ContactForm
from .decorators import logged_in, not_logged_in
from flask_mail import Mail, Message

#app.secret_key = 'this will prevent CSRF attacks' #hidden tag?

@app.route('/')
@app.route('/index')
def index():
    if 'idToken' in session:
        return render_template('index.html', logged_in=True)
    else:
        return render_template('index.html', logged_in=False)


@app.route('/signup', methods=['GET', 'POST'])
@not_logged_in
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        try:
            user = auth.create_user_with_email_and_password(form.email.data,
                form.password.data)
            auth.send_email_verification(user['idToken'])

            uid = user['localId']

            userdata = {
                'uid': uid,
                'firstname': form.firstname.data,
                'lastname': form.lastname.data,
                'email': form.email.data,
                'enabled': True
            }
            db.child('users').child(uid).set(userdata, user['idToken'])

            flash('Thanks for signing up! Please verify your email to log in.')
            return redirect(url_for('login'))
        except HTTPError as e:
            # TODO more accurate error reporting -- pyrebase problem?
            #flash('An account already exists for that email address!')
            flash('Account creation failed.')
            print(e)
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html', form=form, logged_in=False)


@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = auth.sign_in_with_email_and_password(form.email.data,
                form.password.data)
            accountInfo = auth.get_account_info(user['idToken'])

            if (not accountInfo['users'][0]['emailVerified']):
                flash('Please verify your email address!')
            else:
                # create new user session
                session['idToken'] = user['idToken']
                uid = accountInfo['users'][0]['localId']
                session['uid'] = uid
                flash('Login complete for uid="%s"' % uid)
        except HTTPError as e:
            flash('Sorry, we couldn\'t find those credentials!')
            print(e)

        return redirect(url_for('index'))
    else:
        return render_template('login.html', title='Sign in', form=form, logged_in=False)


@app.route('/resetpassword', methods=['GET', 'POST'])
@not_logged_in
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        auth.send_password_reset_email(form.email.data)
        return redirect(url_for('login'))
    return render_template('resetpassword.html', title='Reset', form=form)

@app.route('/edit', methods=['GET', 'POST'])
@logged_in
def edit():
    # TODO prepopulate form with existing profile
    #profile = db.child('profiles').child(session['email']).get(session['idToken']).val()

    form = ProfileForm()
    if form.validate_on_submit():
        new_profile = {
            'school': form.school.data,
            'year': form.year.data,
            'major': form.major.data,
            'about': form.about.data,
            'likes': form.likes.data,
            'contactfor': form.contactfor.data,
            'twitter': form.twitter.data,
            'facebook': form.facebook.data,
            'linkedin': form.linkedin.data,
            'website': form.website.data,
            'make_public': form.make_public.data
        }
        db.child('profiles').child(session['uid']).set(new_profile,
            session['idToken'])
        flash('Profile updated.')
        return redirect('/user/%s' % session['uid'])
    else:
        return render_template('edit.html', form=form, logged_in=True)


@app.route('/user/<uid>', methods=['GET', 'POST'])
@logged_in # eventually only require login if make_public == false
def user(uid):
    try:
        user = db.child('users').child(uid).get(session['idToken']).val()
        mail = Mail(app)
        profile = db.child('profiles').child(uid).get(session['idToken']).val()
        print profile
        form = ContactForm(request.form)
        if user is None or profile is None:
            return render_template('error/404.html', logged_in=True)
        if request.method == 'GET':
            return render_template('user.html', user=user, profile=profile, logged_in=True, form = form)
        elif request.method == 'POST':
            if form.validate() == False:
                flash(u'Please write a message', 'danger')
                return render_template('user.html', user=user, profile=profile, logged_in=True, form = form)
            else: 
                msg = Message(subject='Coffee@CU Email', sender='coffeeatcu@gmail.com', recipients=['hm2602@barnard.edu'])
                msg.body = """
                New Message from %s %s
                %s
                %s
                """ % (user['firstname'], user['lastname'], user['email'], form.message.data)
                mail.send(msg)
                flash(u'Sent','success')
                return render_template('user.html', user=user, profile=profile, logged_in=True, form=ContactForm())
    except HTTPError:
        return render_template('error/400.html', logged_in=True)

@app.route('/logout')
@logged_in
def logout():
    session.pop('idToken', None) # end user session
    session.pop('uid', None)
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
