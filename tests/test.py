import pytest
from app import app, get_db_connection
import os
import tempfile

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            conn = get_db_connection()
            conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)')
            conn.execute('CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, category TEXT, amount REAL, note TEXT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            conn.commit()
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_register_login_logout(client):
    # Register
    response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Registered successfully' in response.data

    # Login
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Dashboard' in response.data or b'Logout' in response.data

    # Logout
    response = client.post('/logout', follow_redirects=True)
    assert b'logged out' in response.data

def test_add_transaction(client):
    # Register + Login
    client.post('/register', data={'username': 'tester', 'password': 'pass'}, follow_redirects=True)
    client.post('/login', data={'username': 'tester', 'password': 'pass'}, follow_redirects=True)

    # Add transaction directly to DB (simulate)
    conn = get_db_connection()
    conn.execute("INSERT INTO transactions (username, type, category, amount, note) VALUES (?, ?, ?, ?, ?)",
                 ('tester', 'income', 'Salary', 5000, 'Monthly salary'))
    conn.commit()
    conn.close()

    # Access dashboard
    response = client.get('/dashboard')
    assert b'Salary' in response.data or b'5000' in response.data
