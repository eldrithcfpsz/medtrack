"""Integration tests for the Flask routes in app.py."""
import database
from conftest import register, login, add_med


# -------------------- AUTH --------------------

def test_register_page_loads(client):
    resp = client.get('/register')
    assert resp.status_code == 200


def test_register_creates_user_and_logs_in(client):
    resp = register(client, 'alice', 'password123')
    # Successful registration redirects to the index.
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')
    with client.session_transaction() as sess:
        assert sess['username'] == 'alice'
        assert 'user_id' in sess


def test_register_duplicate_username_shows_error(client):
    register(client, 'alice', 'password123')
    client.get('/logout')
    resp = client.post(
        '/register',
        data={'username': 'alice', 'password': 'otherpassword'},
    )
    assert resp.status_code == 200
    assert b'Username already exists.' in resp.data


def test_register_missing_fields_shows_error(client):
    resp = client.post('/register', data={'username': '', 'password': ''})
    assert resp.status_code == 200
    assert b'Please fill in all fields.' in resp.data


def test_register_short_password_rejected(client):
    resp = client.post('/register', data={'username': 'shorty', 'password': '1'})
    assert resp.status_code == 200
    assert b'at least 8 characters' in resp.data
    # No user should have been created and no session started.
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
    db = database.get_db()
    rows = db.execute('SELECT * FROM users WHERE username = ?', ('shorty',)).fetchall()
    db.close()
    assert rows == []


def test_register_eight_char_password_accepted(client):
    resp = client.post('/register', data={'username': 'longpw', 'password': '12345678'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_register_while_logged_in_redirects(user_client):
    resp = user_client.get('/register')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_login_page_loads(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_login_with_correct_credentials(client):
    register(client, 'alice', 'password123')
    client.get('/logout')
    resp = login(client, 'alice', 'password123')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_login_with_wrong_password_shows_error(client):
    register(client, 'alice', 'password123')
    client.get('/logout')
    resp = client.post('/login', data={'username': 'alice', 'password': 'wrong'})
    assert resp.status_code == 200
    assert b'Wrong username or password.' in resp.data


def test_login_missing_fields_shows_error(client):
    resp = client.post('/login', data={'username': '', 'password': ''})
    assert resp.status_code == 200
    assert b'Please fill in all fields.' in resp.data


def test_logout_clears_session(user_client):
    resp = user_client.get('/logout')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')
    with user_client.session_transaction() as sess:
        assert 'user_id' not in sess


def test_before_request_clears_session_for_missing_user(user_client):
    # Wipe the users table out from under the active session.
    db = database.get_db()
    db.execute('DELETE FROM users')
    db.commit()
    db.close()
    resp = user_client.get('/')
    # Session was cleared, so the index redirects to login.
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


# -------------------- ADMIN --------------------

def test_admin_login_redirects_to_admin(client):
    resp = login(client, 'admin', 'admin')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/admin')


def test_admin_dashboard_accessible_to_admin(client):
    login(client, 'admin', 'admin')
    resp = client.get('/admin')
    assert resp.status_code == 200


def test_admin_requires_login(client):
    resp = client.get('/admin')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_admin_forbidden_for_regular_user(user_client):
    resp = user_client.get('/admin')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_admin_redirected_from_index_and_add(client):
    login(client, 'admin', 'admin')
    assert client.get('/').headers['Location'].endswith('/admin')
    assert client.get('/add').headers['Location'].endswith('/admin')


def test_admin_dashboard_lists_users_and_meds(client):
    # A regular user with one medication.
    register(client, 'alice', 'password123')
    add_med(client, name='Vitamin D', stock='3')
    client.get('/logout')

    login(client, 'admin', 'admin')
    resp = client.get('/admin')
    assert resp.status_code == 200
    assert b'alice' in resp.data
    assert b'Vitamin D' in resp.data


# -------------------- INDEX / AUTH GUARDS --------------------

def test_index_requires_login(client):
    resp = client.get('/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_index_lists_user_medications(user_client):
    add_med(user_client, name='Aspirin')
    resp = user_client.get('/')
    assert resp.status_code == 200
    assert b'Aspirin' in resp.data


# -------------------- ADD --------------------

def test_add_page_loads(user_client):
    resp = user_client.get('/add')
    assert resp.status_code == 200


def test_add_valid_medication(user_client):
    resp = add_med(user_client, name='Aspirin', stock='10')
    assert resp.status_code == 302
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications WHERE name = ?', ('Aspirin',)).fetchall()
    db.close()
    assert len(rows) == 1
    assert rows[0]['stock'] == 10


def test_add_invalid_medication_shows_error(user_client):
    resp = add_med(user_client, name='', stock='10')
    assert resp.status_code == 200
    assert b'Please fill in all required fields correctly.' in resp.data
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


def test_add_rejects_dosage_over_1000mg(user_client):
    resp = add_med(user_client, name='Aspirin', dosage='1001mg')
    assert resp.status_code == 200
    assert b'Please fill in all required fields correctly.' in resp.data
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


def test_add_rejects_nonstandard_dosage(user_client):
    resp = add_med(user_client, name='Aspirin', dosage='333mg')
    assert resp.status_code == 200
    assert b'Please fill in all required fields correctly.' in resp.data
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


def test_add_page_renders_dosage_options(user_client):
    resp = user_client.get('/add')
    assert resp.status_code == 200
    assert b'<select name="dosage"' in resp.data
    assert b'>500 mg<' in resp.data


def test_add_rejects_frequency_over_5(user_client):
    resp = add_med(user_client, name='Aspirin', frequency='6')
    assert resp.status_code == 200
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


def test_add_rejects_overlong_name(user_client):
    resp = add_med(user_client, name='A' * 51)
    assert resp.status_code == 200
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


def test_add_accepts_dosage_at_1000mg(user_client):
    resp = add_med(user_client, name='Aspirin', dosage='1000mg', frequency='5')
    assert resp.status_code == 302
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert len(rows) == 1


def test_add_requires_login(client):
    resp = add_med(client)
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


# -------------------- EDIT --------------------

def _first_med_id(username_owned=True):
    db = database.get_db()
    row = db.execute('SELECT id FROM medications ORDER BY id LIMIT 1').fetchone()
    db.close()
    return row['id']


def test_edit_page_loads(user_client):
    add_med(user_client, name='Aspirin')
    med_id = _first_med_id()
    resp = user_client.get(f'/edit/{med_id}')
    assert resp.status_code == 200
    assert b'Aspirin' in resp.data


def test_edit_updates_medication(user_client):
    add_med(user_client, name='Aspirin', stock='10')
    med_id = _first_med_id()
    resp = user_client.post(
        f'/edit/{med_id}',
        data={'name': 'Ibuprofen', 'dosage': '200mg', 'frequency': '3', 'stock': '20', 'notes': 'updated'},
    )
    assert resp.status_code == 302
    db = database.get_db()
    med = db.execute('SELECT * FROM medications WHERE id = ?', (med_id,)).fetchone()
    db.close()
    assert med['name'] == 'Ibuprofen'
    assert med['stock'] == 20


def test_edit_invalid_shows_error(user_client):
    add_med(user_client, name='Aspirin')
    med_id = _first_med_id()
    resp = user_client.post(
        f'/edit/{med_id}',
        data={'name': '', 'dosage': '200mg', 'frequency': '3', 'stock': '20', 'notes': ''},
    )
    assert resp.status_code == 200
    assert b'Please fill in all required fields correctly.' in resp.data


def test_edit_nonexistent_redirects(user_client):
    resp = user_client.get('/edit/9999')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


# -------------------- DELETE --------------------

def test_delete_removes_medication(user_client):
    add_med(user_client, name='Aspirin')
    med_id = _first_med_id()
    resp = user_client.get(f'/delete/{med_id}')
    assert resp.status_code == 302
    db = database.get_db()
    rows = db.execute('SELECT * FROM medications').fetchall()
    db.close()
    assert rows == []


# -------------------- TAKE --------------------

def test_take_decrements_stock(user_client):
    add_med(user_client, name='Aspirin', stock='5')
    med_id = _first_med_id()
    user_client.get(f'/take/{med_id}')
    db = database.get_db()
    med = db.execute('SELECT * FROM medications WHERE id = ?', (med_id,)).fetchone()
    db.close()
    assert med['stock'] == 4


def test_take_does_not_go_below_zero(user_client):
    add_med(user_client, name='Aspirin', stock='0')
    med_id = _first_med_id()
    user_client.get(f'/take/{med_id}')
    db = database.get_db()
    med = db.execute('SELECT * FROM medications WHERE id = ?', (med_id,)).fetchone()
    db.close()
    assert med['stock'] == 0


# -------------------- USER ISOLATION --------------------

def test_user_cannot_see_other_users_medication(client):
    register(client, 'alice', 'password123')
    add_med(client, name='AliceMed')
    client.get('/logout')

    register(client, 'bob', 'password123')
    resp = client.get('/')
    assert b'AliceMed' not in resp.data


def test_user_cannot_edit_other_users_medication(client):
    register(client, 'alice', 'password123')
    add_med(client, name='AliceMed', stock='10')
    alice_med_id = _first_med_id()
    client.get('/logout')

    register(client, 'bob', 'password123')
    # Bob tries to edit Alice's medication -> redirected, no change.
    resp = client.post(
        f'/edit/{alice_med_id}',
        data={'name': 'Hacked', 'dosage': 'x', 'frequency': '1', 'stock': '1', 'notes': ''},
    )
    assert resp.status_code == 302
    db = database.get_db()
    med = db.execute('SELECT * FROM medications WHERE id = ?', (alice_med_id,)).fetchone()
    db.close()
    assert med['name'] == 'AliceMed'


def test_user_cannot_delete_other_users_medication(client):
    register(client, 'alice', 'password123')
    add_med(client, name='AliceMed')
    alice_med_id = _first_med_id()
    client.get('/logout')

    register(client, 'bob', 'password123')
    client.get(f'/delete/{alice_med_id}')
    db = database.get_db()
    med = db.execute('SELECT * FROM medications WHERE id = ?', (alice_med_id,)).fetchone()
    db.close()
    assert med is not None  # still there


# -------------------- PROFILE --------------------

def test_profile_requires_login(client):
    resp = client.get('/profile')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/login')


def test_profile_page_loads(user_client):
    resp = user_client.get('/profile')
    assert resp.status_code == 200


def test_profile_update_persists(user_client):
    resp = user_client.post(
        '/profile',
        data={'first_name': 'Alice', 'last_name': 'Smith', 'age': '30', 'height': '170', 'weight': '65'},
    )
    assert resp.status_code == 302
    with user_client.session_transaction() as sess:
        user_id = sess['user_id']
    db = database.get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    assert user['first_name'] == 'Alice'
    assert user['age'] == 30


def test_profile_update_with_blank_numeric_fields(user_client):
    # Empty optional numeric fields should be stored as NULL, not crash.
    resp = user_client.post(
        '/profile',
        data={'first_name': 'Alice', 'last_name': '', 'age': '', 'height': '', 'weight': ''},
    )
    assert resp.status_code == 302
    with user_client.session_transaction() as sess:
        user_id = sess['user_id']
    db = database.get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    assert user['age'] is None
