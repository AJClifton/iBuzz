import flask_login


class User(flask_login.UserMixin):
    def __init__(self, user_id, first_name, email, password):
        self.id = user_id
        self.first_name = first_name
        self.email = email
        self.password = password

