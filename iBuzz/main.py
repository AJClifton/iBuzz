import sqlite3
import flask
import flask_login
import database
import error_logger
import login_database
import notifications
import yaml

config = yaml.safe_load(open("config.yaml"))
app = flask.Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = config["secret_key"]
db = database.Database()
login_db = login_database.LoginDatabase()
login_manager = flask_login.LoginManager(app)
login_manager.login_view = "login"
notification = notifications.Notifications(config["notifications_email"], config["notifications_email_password"], login_db)

def create_app():
    app.run()

@app.route('/', methods=['GET'])
def redirect_user():
    if flask_login.current_user.is_authenticated:
        return dashboard()
    return login()


@app.route('/', methods=['POST'])
def receive_json():
    json = flask.request.json
    print(json)
    db.data_received(json, notification.evaluate)
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
    try:
        if login_database.verify_password(user, password):
            flask_login.login_user(user, remember=bool(remember))
            return flask.redirect('/dashboard')
    except Exception:
        return login()


@app.route('/signup', methods=['GET'])
def signup():
    return flask.render_template('signup/signup.html')


@app.route('/signup', methods=['POST'])
def signup_post():
    email = flask.request.form.get('email')
    print(email)
    if login_db.fetch_user_by_email(email) is not None:
        return signup()
    name = flask.request.form.get('name')
    password = flask.request.form.get('password')
    password_repeat = flask.request.form.get('password_repeat')
    if password != password_repeat:
        return signup()
    login_db.add_user(name, email, password)
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


@app.route('/settings', methods=['GET'])
@flask_login.login_required
def settings():
    return flask.render_template('settings/settings.html')


@app.route('/export', methods=['GET'])
@flask_login.login_required
def export():
    return flask.render_template('export/export.html')


@app.route('/templates/<path:path>')
def send_template(path):
    return flask.send_from_directory('templates', path)


@app.route('/data/<path:path>', methods=['GET'])
@flask_login.login_required
def fetch_data(path):
    try:
        serial_number, hive_number, field, *start_time = path.split("/")
        if not login_db.check_visibility_permissions(flask_login.current_user.id, serial_number):
            return '', 400
        return db.fetch_field(serial_number, hive_number, field, (0 if len(start_time) == 0 else start_time[0]))
    except KeyError as e:
        error_logger.log_error(e)
        return {}


@app.route('/names', methods=['GET'])
def fetch_names():
    return {'names': db.fetch_names()}


@app.route('/serial_numbers', methods=['GET'])
@flask_login.login_required
def fetch_serial_numbers():
    return {'serial_numbers': login_db.fetch_visible_serial_numbers(flask_login.current_user.id)}


@app.route('/owned_serial_numbers', methods=['GET'])
@flask_login.login_required
def fetch_owned_serial_numbers():
    return {'owned_serial_numbers': login_db.fetch_owned_serial_numbers(flask_login.current_user.id)}


@app.route('/hive_numbers/<path:path>', methods=['GET'])
@flask_login.login_required
def fetch_hive_numbers(path):
    if login_db.check_visibility_permissions(flask_login.current_user.id, path):
        return {'hive_numbers': db.fetch_hive_numbers(path)}
    else:
        return '', 400


@app.route('/recent_values/<path:path>', methods=['GET'])
@flask_login.login_required
def fetch_recent_values(path):
    if login_db.check_visibility_permissions(flask_login.current_user.id, path):
        return {'recent_values': db.fetch_most_recent_values(path)}
    else:
        return '', 400


@app.route('/register/<path:path>')
@flask_login.login_required
def register_hawk(path):
    try:
        login_db.register_hawk(flask_login.current_user.id, path)
    except (ValueError, sqlite3.IntegrityError) as e:
        return '', 400
    return '', 200


@app.route('/deregister/<path:path>')
@flask_login.login_required
def deregister_hawk(path):
    try:
        login_db.deregister_hawk(flask_login.current_user.id, path)
    except PermissionError as e:
        return '', 400
    return '', 200


@app.route('/add_visibility/<path:path>')
@flask_login.login_required
def add_hawk_visibility(path):
    try:
        serial_number, user_id, *other = path.split('/')
        # if user-id is actually an email, fetch the user_id
        if '@' in user_id:
            user_id = login_db.fetch_user_by_email(user_id).id
        login_db.add_hawk_visibility(flask_login.current_user.id, serial_number, user_id)
    except (ValueError, PermissionError) as e:
        return '', 400
    return '', 200


@app.route('/remove_visibility/<path:path>')
@flask_login.login_required
def remove_hawk_visibility(path):
    try:
        serial_number, user_id, *other = path.split('/')
        # if user-id is actually an email, fetch the user_id
        if '@' in user_id:
            user_id = login_db.fetch_user_by_email(user_id).id
        login_db.remove_hawk_visibility(flask_login.current_user.id, serial_number, user_id)
    except (ValueError, PermissionError) as e:
        return '', 400
    return '', 200


@app.route('/visibility/<path:path>')
@flask_login.login_required
def fetch_hawk_visibility(path):
    try:
        serial_number, *other = path.split('/')
        return {'visibility': login_db.fetch_all_visibility_permissions(flask_login.current_user.id, serial_number)}
    except PermissionError as e:
        return '', 400


@app.route('/add_notification/<path:path>')
@flask_login.login_required
def add_notification(path):
    try:
        serial_number, hive_number, sensor, sign, value, *other = path.split('/')
    except ValueError:
        serial_number, sensor, sign, value, *other = path.split('/')
        hive_number = None
    try:
        login_db.add_notification(flask_login.current_user.id, serial_number, hive_number, sensor, sign, value)
    except PermissionError:
        return '', 403
    except ValueError:
        return '', 400
    return '', 200


@app.route('/remove_notification/<path:path>')
@flask_login.login_required
def remove_notification(path):
    try:
        login_db.remove_notification(flask_login.current_user.id, path)
    except PermissionError:
        return '', 400
    return '', 200


@app.route('/notifications')
@flask_login.login_required
def fetch_notifications():
    return {'notifications': login_db.fetch_notifications(user_id=flask_login.current_user.id)}


@app.route('/download_replay/<path:path>')
@flask_login.login_required
def download_replay_log(path):
    if login_db.check_hawk_ownership(flask_login.current_user.id, path):
        return flask.send_file('replay_logs/' + path + ".txt", as_attachment=True)
    else:
        return '', 403
    

@app.route('/download_data/<path:path>')
@flask_login.login_required
def download_data(path):
    if login_db.check_visibility_permissions(flask_login.current_user.id, path):
        return db.data_to_csv(path), {"Content-Type": "text/csv"}
    else:
        return '', 403