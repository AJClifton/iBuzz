import os
import unittest
import uuid

import login_database


class UserAccounts(unittest.TestCase):
    login_db_path = "login_test.db"
    database_path = "database_test.db"

    def setUp(self):
        self.login_db = login_database.LoginDatabase(self.login_db_path)

    def test_add_user(self):
        self.login_db.add_user("Alex", "alex@test.com", "password")
        user = self.login_db.fetch_user_by_email("alex@test.com")
        self.assertEqual(user.first_name, "Alex", "Wrong first name returned")
        user_id = user.id

        self.login_db.add_user("William", "alex@test.com", "password")
        user = self.login_db.fetch_user_by_email("alex@test.com")
        self.assertEqual(user.first_name, "Alex", "Name overwritten with new registration")

        self.assertEqual(self.login_db.fetch_user(user_id).first_name, "Alex", "Error with the user_id")

        self.assertFalse(self.login_db.check_unique_user_id(user_id))
        new_id = str(uuid.uuid4())
        while new_id == user_id:
            new_id = str(uuid.uuid4())
        self.assertTrue(self.login_db.check_unique_user_id(new_id))

    def tearDown(self):
        self.login_db.close()
        os.remove(self.login_db_path)


if __name__ == '__main__':
    unittest.main()
