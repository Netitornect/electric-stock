from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# สร้างโฟลเดอร์ uploads ถ้ายังไม่มี
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------- เตรียมฐานข้อมูล ----------
def init_db():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        category TEXT,
        quantity INTEGER,
        image_name TEXT,
        last_updated TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE
    )''')
    conn.commit()
    conn.close()

# ---------- หน้าแรก ----------
@app.route('/')
def index():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    items = c.fetchall()
    c.execute("SELECT name FROM categories ORDER BY name")
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return render_template('index.html', items=items, categories=categories)

# ---------- รับสินค้าเข้า ----------
@app.route('/add', methods=['POST'])
def add_item():
    name = request.form['name']
    category = request.form['category']
    qty = int(request.form['quantity'])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    image_name = None
    image = request.files.get('image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_name = filename

    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE name=? AND category=?", (name, category))
    result = c.fetchone()

    if result:
        new_qty = result[3] + qty
        c.execute("UPDATE products SET quantity=?, last_updated=? WHERE name=? AND category=?",
                  (new_qty, now, name, category))
    else:
        c.execute("INSERT INTO products (name, category, quantity, image_name, last_updated) VALUES (?, ?, ?, ?, ?)",
                  (name, category, qty, image_name, now))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- ขายสินค้าออก ----------
@app.route('/sell', methods=['POST'])
def sell_item():
    name = request.form['name']
    category = request.form['category']
    qty = int(request.form['quantity'])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE name=? AND category=?", (name, category))
    result = c.fetchone()

    if result and result[3] >= qty:
        new_qty = result[3] - qty
        c.execute("UPDATE products SET quantity=?, last_updated=? WHERE name=? AND category=?",
                  (new_qty, now, name, category))
    conn.commit()
    conn.close()
    return redirect('/')

# ---------- เพิ่มหมวดหมู่ ----------
@app.route('/add_category', methods=['POST'])
def add_category():
    new_category = request.form['new_category'].strip()
    if new_category:
        conn = sqlite3.connect('stock.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO categories (name) VALUES (?)", (new_category,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # หมวดซ้ำจะไม่เพิ่ม
        conn.close()
    return redirect('/')

# ---------- รายงานคงคลัง ----------
@app.route('/report')
def report():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT category, SUM(quantity) FROM products GROUP BY category")
    summary = c.fetchall()
    conn.close()
    return render_template('report.html', summary=summary)

# ---------- แสดงภาพ ----------
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------- เริ่มทำงาน ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)