from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_goods():
    conn = get_db_connection()
    goods = conn.execute("SELECT title, img, comments, price FROM magazin").fetchall()
    conn.close()
    return goods

def add_to_corz(title, price, user_id):
    conn = get_db_connection()
    conn.execute("INSERT INTO corz (title, price, user_id) VALUES (?, ?, ?)", (title, price, user_id))
    conn.commit()
    conn.close()

def get_cart_items(user_id):
    conn = get_db_connection()
    cart_items = conn.execute("SELECT id, title, price FROM corz WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return cart_items

def remove_from_corz(item_id, user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM corz WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()

def get_cart_total(user_id):
    conn = get_db_connection()
    total = conn.execute("SELECT SUM(price) AS total FROM corz WHERE user_id = ?", (user_id,)).fetchone()['total']
    conn.close()
    return total if total else 0

def add_payment(user_id, total_amount, card_number, card_expiry, card_cvv):
    conn = get_db_connection()
    conn.execute("INSERT INTO oplata (user_id, total_amount, card_number, card_expiry, card_cvv) VALUES (?, ?, ?, ?, ?)",
                 (user_id, total_amount, card_number, card_expiry, card_cvv))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    goods = get_goods()
    return render_template('index.html', goods=goods)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['pass']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE login = ? AND pass = ?', (login, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('index'))
        else:
            return 'Неверный логин или пароль'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        name = request.form['name']
        password = request.form['pass']
        conn = get_db_connection()
        conn.execute('INSERT INTO users (login, name, pass) VALUES (?, ?, ?)', (login, name, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('reg.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('index'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    title = request.form.get('title')
    price = request.form.get('price')
    
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    add_to_corz(title, price, user_id)

    return redirect(url_for('index'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item_id = request.form.get('item_id')
    
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    remove_from_corz(item_id, user_id)

    return redirect(url_for('corz'))

@app.route('/corz')
def corz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = get_cart_items(user_id)
    total_amount = get_cart_total(user_id)
    return render_template('corz.html', cart=cart_items, total_amount=total_amount)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    total_amount = get_cart_total(user_id)
    
    if request.method == 'POST':
        card_number = request.form['card_number']
        card_expiry = request.form['card_expiry']
        card_cvv = request.form['card_cvv']
        
        add_payment(user_id, total_amount, card_number, card_expiry, card_cvv)
        
        # Clear the cart after payment
        conn = get_db_connection()
        conn.execute("DELETE FROM corz WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))

    return render_template('checkout.html', total_amount=total_amount)

if __name__ == '__main__':
    app.run(debug=True)
