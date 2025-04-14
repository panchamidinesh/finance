# import pytest
# from app import app, get_db_connection
# import os
# import tempfile

# @pytest.fixture
# def client():
#     db_fd, db_path = tempfile.mkstemp()
#     app.config['DATABASE'] = db_path
#     app.config['TESTING'] = True
#     app.config['WTF_CSRF_ENABLED'] = False

#     with app.test_client() as client:
#         with app.app_context():
#             conn = get_db_connection()
#             conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)')
#             conn.execute('CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, category TEXT, amount REAL, note TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
#             conn.commit()
#         yield client

#     os.close(db_fd)
#     os.unlink(db_path)

# def test_register_login_logout(client):
#     # Register
#     response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
#     assert b'Registered successfully' in response.data

#     # Login
#     response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
#     assert b'Dashboard' in response.data or b'Logout' in response.data

#     # Logout
#     response = client.post('/logout', follow_redirects=True)
#     assert b'logged out' in response.data

# def test_add_transaction(client):
#     # Register + Login
#     client.post('/register', data={'username': 'tester', 'password': 'pass'}, follow_redirects=True)
#     client.post('/login', data={'username': 'tester', 'password': 'pass'}, follow_redirects=True)

#     # Add transaction directly to DB (simulate)
#     conn = get_db_connection()
#     conn.execute("INSERT INTO transactions (username, type, category, amount, note) VALUES (?, ?, ?, ?, ?)",
#                  ('tester', 'income', 'Salary', 5000, 'Monthly salary'))
#     conn.commit()
#     conn.close()

#     # Access dashboard
#     response = client.get('/dashboard')
#     assert b'Salary' in response.data or b'5000' in response.data





import unittest
from app import app, get_db_connection
import os
import tempfile

class FinanceAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()

        with app.app_context():
            conn = get_db_connection()
            conn.execute('DROP TABLE IF EXISTS users')
            conn.execute('DROP TABLE IF EXISTS transactions')
            conn.execute('''CREATE TABLE users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL UNIQUE,
                                password TEXT NOT NULL
                            )''')
            conn.execute('''CREATE TABLE transactions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT NOT NULL,
                                type TEXT NOT NULL,
                                category TEXT NOT NULL,
                                amount REAL NOT NULL,
                                note TEXT,
                                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )''')
            conn.commit()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

    def test_home_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_register_login_dashboard_logout(self):
        # Register user
        response = self.client.post('/register', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        self.assertIn(b'Registered successfully', response.data)

        # Login
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        self.assertIn(b'Dashboard', response.data)

        # Dashboard access
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'testuser', response.data)

        # Logout
        response = self.client.post('/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', response.data)

    def test_login_invalid_credentials(self):
        response = self.client.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials', response.data)

if __name__ == '__main__':
    unittest.main()
