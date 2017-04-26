from app import auth, db, firebase
from requests.exceptions import HTTPError


def create_new_user(email, password, firstname, lastname):
    try:
        user = auth.create_user_with_email_and_password(email, password)
        auth.send_email_verification(user['idToken'])
        uid = user['localId']

        userdata = {
            'uid': uid,
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'enabled': True
        }
        db.child('users').child(uid).set(userdata)

        return True
    except HTTPError as e:
        return False


def sign_in_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user['idToken']
    except HTTPError as e:
        return None


def get_userdata(uid):
    return db.child('users').child(uid).get().val()


def is_verified(id_token):
    account_info = auth.get_account_info(id_token)
    return account_info['users'][0]['emailVerified']


def uid_from_id_token(id_token):
    account_info = auth.get_account_info(id_token)
    return account_info['users'][0]['localId']


def get_profile(uid):
    return db.child('profiles').child(uid).get().val()


def set_profile(uid, profile):
    db.child('profiles').child(uid).set(profile)


def get_user_profile_pairs():
    all_users = db.child('users').get()
    pairs = []
    for user in all_users.each():
        profile = get_profile(user.key())
        # only show enabled users who have completed their profiles
        if user.val()['enabled'] and profile:
            pairs.append((user.val(), profile))
    return pairs
