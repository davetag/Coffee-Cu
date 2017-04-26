from flask import flash, redirect, render_template, request, session, url_for
from app import app, auth, db, firebase, mail
from .forms import (ContactForm, LoginForm, ProfileForm, ResetPasswordForm,
    SignupForm)
from .decorators import logged_in, not_logged_in
from .dbhelpers import (create_new_user, sign_in_user, is_verified,
    uid_from_id_token, get_profile, set_profile, get_userdata,
    get_user_profile_pairs)
from .mailhelpers import send_contact_email


@app.route('/')
@app.route('/index')
def index():
    if 'idToken' in session:
        pairs = get_user_profile_pairs();
        return render_template('index.html', logged_in=True, pairs=pairs)
    else:
        return render_template('index.html', logged_in=False)


@app.route('/signup', methods=['GET', 'POST'])
@not_logged_in
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        firstname = form.firstname.data
        lastname = form.lastname.data

        if create_new_user(email, password, firstname, lastname):
            flash('Thanks for signing up! Please verify your email to log in.')
            return redirect(url_for('login'))
        else:
            flash('An account already exists for that email address!')
            return redirect(url_for('signup'))
    else:
        return render_template('signup.html', form=form, logged_in=False)


@app.route('/login', methods=['GET', 'POST'])
@not_logged_in
def login():
    form = LoginForm()
    if form.validate_on_submit():
        id_token = sign_in_user(form.email.data, form.password.data)
        if id_token is not None:
            if is_verified(id_token):
                session['idToken'] = id_token
                session['uid'] = uid_from_id_token(id_token)
            else:
                flash('Please verify your email address!')
        else:
            flash('Sorry, we couldn\'t find those credentials!')
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
    profile = get_profile(session['uid'])

    # if user already made a profile, populate form with the information
    form = None
    if profile is not None:
        # TODO is there a clean way to do this?  can't pass in a dict...
        form = ProfileForm(school=profile['school'], year=profile['year'],
            major=profile['major'], about=profile['about'],
            likes=profile['likes'], contactfor=profile['contactfor'])
    else:
        form = ProfileForm()

    if form.validate_on_submit():
        new_profile = {
            'school': form.school.data,
            'year': form.year.data,
            'major': form.major.data,
            'about': form.about.data,
            'likes': form.likes.data,
            'contactfor': form.contactfor.data
        }
        # TODO eventually add new profile to queue of pending profiles
        # instead of immediately updating with no moderator approval
        set_profile(session['uid'], new_profile)
        flash('Profile updated.')
        return redirect('/user/%s' % session['uid'])
    else:
        return render_template('edit.html', form=form, logged_in=True)


@app.route('/user/<uid>', methods=['GET', 'POST'])
@logged_in # eventually only require login if make_public == false
def user(uid):
    try:
        # get info for user to display, 404 if not found
        viewed_user = get_userdata(uid)
        profile = get_profile(uid)

        if viewed_user is None or profile is None:
            return render_template('error/404.html', logged_in=True)

        form = ContactForm(request.form)
        if request.method == 'POST':
            user = get_userdata(session['uid'])
            if form.validate():
                send_contact_email(viewed_user['email'], user['firstname'],
                    user['lastname'], form.message.data)
                flash('Sent message to %s!' % viewed_user['firstname'])
            else:
                flash('Please write a message')

        # in all other cases, just display
        return render_template('user.html', viewed_user=viewed_user,
            profile=profile, logged_in=True, form=form)
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
