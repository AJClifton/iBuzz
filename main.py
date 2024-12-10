import sqlite3

import flask
import flask_login
import database
import error_logger
import login_database

app = flask.Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'iBuzz2FourthYearGroupDevelopmentProject'
db = database.Database()
login_db = login_database.LoginDatabase()
login_manager = flask_login.LoginManager(app)
login_manager.login_view = "login"


@app.route('/', methods=['GET'])
def redirect_user():
    return flask.redirect('/login')


@app.route('/', methods=['POST'])
def receive_json():
    json = flask.request.json
    print(json)
    db.data_received(json)
    return '', 200


@login_manager.user_loader
def load_user(user_id):
    return login_db.fetch_user(user_id)


@app.route('/login', methods=['GET'])
def login():
    return flask.render_template('login/login.html')


@app.route('/login', methods=['POST'])
def login_post():
    email = flask.request.form.get('email')
    password = flask.request.form.get('password')
    remember = flask.request.form.get('remember')
    user = login_db.fetch_user_by_email(email)
    if login_database.verify_password(user, password):
        flask_login.login_user(user, remember=bool(remember))
        return flask.redirect('/dashboard')


@app.route('/signup', methods=['GET'])
def signup():
    return flask.render_template('signup/signup.html')


@app.route('/signup', methods=['POST'])
def signup_post():
    email = flask.request.form.get('email')
    print(email)
    if login_db.fetch_user_by_email(email) is not None:
        return flask.abort(400)
    password = flask.request.form.get('password')
    password_repeat = flask.request.form.get('password_repeat')
    if password != password_repeat:
        return flask.abort(400)
    login_db.add_user("NameHere", email, password)
    return flask.redirect('/login')


@app.route('/logout', methods=['GET'])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return flask.redirect('/login')


@app.route('/dashboard', methods=['GET'])
@flask_login.login_required
def dashboard():
    return flask.render_template('dashboard/dashboard.html')


@app.route('/templates/<path:path>')
def send_template(path):
    return flask.send_from_directory('templates', path)


@app.route('/data/<path:path>')
def fetch_data(path):
    try:
        serial_number, field, *start_time = path.split("/")
        # Check a user is logged in, and if the user has permission to view this data
        if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
            return '', 400
        else:
            if not login_db.check_visibility_permissions(flask_login.current_user.id, serial_number):
                return '', 400
        return db.fetch_field(serial_number, field, 0 if len(start_time) == 0 else start_time[0])
    except KeyError as e:
        error_logger.log_error(e)
        return {}


@app.route('/names')
def fetch_names():
    return {'names': db.fetch_names()}


@app.route('/serial_numbers')
def fetch_serial_numbers():
    if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
        return '', 400
    return {'serial_numbers': login_db.fetch_visible_serial_numbers(flask_login.current_user.id)}


@app.route('/register/<path:path>')
def register_hawk(path):
    try:
        if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
            return '', 400
        else:
            login_db.register_hawk(flask_login.current_user.id, path)
    except (ValueError, sqlite3.IntegrityError) as e:
        return '', 400
    return '', 200


@app.route('/deregister/<path:path>')
def deregister_hawk(path):
    try:
        if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
            return '', 400
        else:
            login_db.deregister_hawk(flask_login.current_user.id, path)
    except (ValueError, PermissionError) as e:
        return '', 400
    return '', 200


@app.route('/addvisibility/<path:path>')
def add_hawk_visibility(path):
    try:
        if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
            return '', 400
        else:
            hawk_id, user_id, *other = path.split('/')
            # if user-id is actually an email, fetch the user_id
            if '@' in user_id:
                user_id = login_db.fetch_user_by_email(user_id).id
            login_db.add_hawk_visibility(flask_login.current_user.id, hawk_id, user_id)
    except (ValueError, PermissionError) as e:
        return '', 400
    return '', 200


@app.route('/removevisibility/<path:path>')
def remove_hawk_visibility(path):
    try:
        if isinstance(flask_login.current_user, flask_login.AnonymousUserMixin):
            return '', 400
        else:
            hawk_id, user_id, *other = path.split('/')
            # if user-id is actually an email, fetch the user_id
            if '@' in user_id:
                user_id = login_db.fetch_user_by_email(user_id).id
            login_db.remove_hawk_visibility(flask_login.current_user.id, hawk_id, user_id)
    except (ValueError, PermissionError) as e:
        return '', 400
    return '', 200
