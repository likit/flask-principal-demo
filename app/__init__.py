from flask import Flask, Response, current_app, request, redirect, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_principal import Principal, Permission, RoleNeed, Identity, identity_changed, AnonymousIdentity, \
    identity_loaded, UserNeed


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username
        self.roles = []


a_user = User(1, 'admin')
a_user.roles.append('admin')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisisasupersecretivekey'
app.debug = True
principals = Principal(app)
login_manager = LoginManager(app)

admin_permission = Permission(RoleNeed('admin'))


@login_manager.user_loader
def load_user(userid):
    return a_user


@app.route('/')
def index():
    return 'This is an index view.'


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user

    # Add the UserNeed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    # Assuming the User model has a list of roles, update the
    # identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role))


@app.route('/login')
def login():
    user = a_user
    login_user(user)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
    return redirect(request.args.get('next', '/'))


@app.route('/logout')
@login_required
def logout():
    # Remove the user information from the session
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(request.args.get('next') or '/')


@app.route('/admin')
@admin_permission.require()
def do_admin_index():
    return Response('Only if your an admin.')


@app.route('/articles')
def do_articles():
    with admin_permission.require():
        return Response('Only if your an admin.')
