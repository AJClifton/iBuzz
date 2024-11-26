import flask
import flask_login
import database
import login_database
from user import User

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
    login_db.add_user(email, password)
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
def send_report(path):
    return flask.send_from_directory('templates', path)


@app.route('/data/<path:path>')
def fetch_data(path):
    return db.fetch_data(path)
