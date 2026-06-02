from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db, init_db
from logic import is_stock_low, is_valid_medication, is_valid_password, MIN_PASSWORD_LENGTH, ALLOWED_DOSAGES_MG

app = Flask(__name__)
app.secret_key = 'medtrack_secret_key'

@app.before_request
def check_session():
    if 'user_id' in session:
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()
        if not user:
            session.clear()
# -------------------- AUTH --------------------


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='Please fill in all fields.')
        if not is_valid_password(password):
            return render_template('register.html', error=f'Password must be at least {MIN_PASSWORD_LENGTH} characters.')
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        except:
            return render_template('register.html', error='Username already exists.')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('username') == 'admin':
            return redirect(url_for('admin'))
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('login.html', error='Please fill in all fields.')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        db.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            if user['username'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        return render_template('login.html', error='Wrong username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------- ADMIN --------------------

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('username') != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    users = db.execute('SELECT * FROM users WHERE username != "admin"').fetchall()
    medications = db.execute('''
        SELECT m.*, u.username
        FROM medications m
        JOIN users u ON m.user_id = u.id
        ORDER BY m.id DESC
    ''').fetchall()
    total_users = len(users)
    total_meds = len(medications)
    low_stock_meds = [m for m in medications if is_stock_low(m['stock'])]
    db.close()
    return render_template('admin.html',
        users=users,
        medications=medications,
        total_users=total_users,
        total_meds=total_meds,
        low_stock_meds=low_stock_meds
    )

# -------------------- PROFILE --------------------

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        age = request.form.get('age', '')
        height = request.form.get('height', '')
        weight = request.form.get('weight', '')
        age = int(age) if age else None
        height = int(height) if height else None
        weight = int(weight) if weight else None
        db.execute(
            'UPDATE users SET first_name=?, last_name=?, age=?, height=?, weight=? WHERE id=?',
            (first_name, last_name, age, height, weight, session['user_id'])
        )
        db.commit()
        db.close()
        return redirect(url_for('profile'))
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    db.close()
    return render_template('profile.html', user=user)

# -------------------- MEDICATIONS --------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('username') == 'admin':
        return redirect(url_for('admin'))
    db = get_db()
    medications = db.execute(
        'SELECT * FROM medications WHERE user_id = ? ORDER BY id DESC',
        (session['user_id'],)
    ).fetchall()
    db.close()
    low_stock = [m for m in medications if is_stock_low(m['stock'])]
    return render_template('index.html', medications=medications, low_stock=low_stock)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('username') == 'admin':
        return redirect(url_for('admin'))
    if request.method == 'POST':
        name = request.form.get('name', '')
        dosage = request.form.get('dosage', '')
        frequency = request.form.get('frequency', '')
        stock = request.form.get('stock', '')
        notes = request.form.get('notes', '')
        if not is_valid_medication(name, dosage, frequency, stock):
            return render_template('add.html', error='Please fill in all required fields correctly.', dosages=ALLOWED_DOSAGES_MG)
        db = get_db()
        db.execute(
            'INSERT INTO medications (user_id, name, dosage, frequency, stock, notes) VALUES (?, ?, ?, ?, ?, ?)',
            (session['user_id'], name, dosage, frequency, int(stock), notes)
        )
        db.commit()
        db.close()
        return redirect(url_for('index'))
    return render_template('add.html', dosages=ALLOWED_DOSAGES_MG)

@app.route('/edit/<int:med_id>', methods=['GET', 'POST'])
def edit(med_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('username') == 'admin':
        return redirect(url_for('admin'))
    db = get_db()
    med = db.execute(
        'SELECT * FROM medications WHERE id = ? AND user_id = ?',
        (med_id, session['user_id'])
    ).fetchone()
    if not med:
        db.close()
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name', '')
        dosage = request.form.get('dosage', '')
        frequency = request.form.get('frequency', '')
        stock = request.form.get('stock', '')
        notes = request.form.get('notes', '')
        if not is_valid_medication(name, dosage, frequency, stock):
            return render_template('edit.html', med=med, error='Please fill in all required fields correctly.', dosages=ALLOWED_DOSAGES_MG)
        db.execute(
            'UPDATE medications SET name=?, dosage=?, frequency=?, stock=?, notes=? WHERE id=? AND user_id=?',
            (name, dosage, int(frequency), int(stock), notes, med_id, session['user_id'])
        )
        db.commit()
        db.close()
        return redirect(url_for('index'))
    db.close()
    return render_template('edit.html', med=med, dosages=ALLOWED_DOSAGES_MG)

@app.route('/delete/<int:med_id>')
def delete(med_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('username') == 'admin':
        return redirect(url_for('admin'))
    db = get_db()
    db.execute(
        'DELETE FROM medications WHERE id = ? AND user_id = ?',
        (med_id, session['user_id'])
    )
    db.commit()
    db.close()
    return redirect(url_for('index'))

@app.route('/take/<int:med_id>')
def take(med_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('username') == 'admin':
        return redirect(url_for('admin'))
    db = get_db()
    med = db.execute(
        'SELECT * FROM medications WHERE id = ? AND user_id = ?',
        (med_id, session['user_id'])
    ).fetchone()
    if med and med['stock'] > 0:
        db.execute(
            'UPDATE medications SET stock = stock - 1 WHERE id = ? AND user_id = ?',
            (med_id, session['user_id'])
        )
        db.commit()
    db.close()
    return redirect(url_for('index'))

# -------------------- RUN --------------------

if __name__ == '__main__':
    init_db()
    app.run(debug=True)