import flask_login


class User(flask_login.UserMixin):
    def __init__(self, user_id, email, password):
        self.id = user_id
        self.email = email
        self.password = password

