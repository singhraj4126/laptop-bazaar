from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for, flash
import pymysql
from flask_mysqldb import MySQL
import MySQLdb.cursors


# Flask App Initialization
import os
from dotenv import load_dotenv


# 1. Sabse pehle .env file ko load karo
load_dotenv()

app = Flask(__name__)

# 2. Secret Key ko .env se uthao (Agar nahi mili toh default use karega)
app.secret_key = os.getenv('SECRET_KEY', 'laptop_bazaar_secret_key_99')

# 3. Database URL ko .env se uthao
# Agar .env mein DB_URL nahi mili, toh ye error dega (jo ki security ke liye achha hai)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------
# DATABASE MODELS (Sahi Names ke Saath)
# ---------------------------------------------------------

# 1. UPDATED USER MODEL (Naye columns ke saath)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='users')
    rating = db.Column(db.Float, default=4.0)
    # Ye columns checkout ke liye zaroori hain
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
class Product(db.Model):
    __tablename__ = 'laptop' # SQL table 'laptop' se connect karega
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))
    specs = db.Column(db.Text)      # Jo pehle missing tha
    discount = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()
    print("Database Tables Created Successfully!")

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route('/setup')
def setup():
    from sqlalchemy import text
    try:
        # Step 1: Forcefully create all models (User, Product)
        db.create_all()
        
        # Step 2: Ensure Raw SQL tables exist (Cart & Orders)
        # SQLite mein 'AUTOINCREMENT' aise hi likha jata hai
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                laptop_id INTEGER, 
                quantity INTEGER DEFAULT 1
            )
        """))
        
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                full_name TEXT, phone TEXT, address TEXT, city TEXT, pincode TEXT, 
                total_amount REAL, status TEXT DEFAULT 'Pending', 
                payment_mode TEXT DEFAULT 'COD', order_date DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.session.commit()

        # Step 3: Only add laptops if the table is empty
        if Product.query.count() == 0:
            laptops_data = [
            {"name": "MacBook Air M2", "brand": "Apple", "price": 114900, "specs": "8GB RAM, 256GB SSD, 13.6-inch Liquid Retina", "img": "https://m.media-amazon.com/images/I/71f5Eu5lJSL._SL1500_.jpg"},
            {"name": "MacBook Pro M3", "brand": "Apple", "price": 169900, "specs": "16GB RAM, 512GB SSD, 14-inch XDR Display", "img": "https://m.media-amazon.com/images/I/6168-3Yv7eL._SL1500_.jpg"},
            {"name": "Dell XPS 13", "brand": "Dell", "price": 125000, "specs": "i7 12th Gen, 16GB RAM, 512GB SSD", "img": "https://m.media-amazon.com/images/I/71jG+e7roXL._SL1500_.jpg"},
            {"name": "Dell Inspiron 15", "brand": "Dell", "price": 54000, "specs": "i5 11th Gen, 8GB RAM, 512GB SSD", "img": "https://m.media-amazon.com/images/I/61G5yV9+3tL._SL1500_.jpg"},
            {"name": "HP Spectre x360", "brand": "HP", "price": 135000, "specs": "Touchscreen, i7 13th Gen, 16GB RAM", "img": "https://m.media-amazon.com/images/I/719f6A2y6dL._SL1500_.jpg"},
            {"name": "HP Victus Gaming", "brand": "HP", "price": 68000, "specs": "Ryzen 7, RTX 3050Ti, 16GB RAM", "img": "https://m.media-amazon.com/images/I/71-fS9iI6sL._SL1500_.jpg"},
            {"name": "ASUS ROG Zephyrus G14", "brand": "ASUS", "price": 145000, "specs": "Ryzen 9, RTX 4060, Anime Matrix", "img": "https://m.media-amazon.com/images/I/717S+O6W0ML._SL1500_.jpg"},
            {"name": "ASUS TUF Gaming F15", "brand": "ASUS", "price": 72000, "specs": "i5 11th Gen, RTX 3050, 144Hz Screen", "img": "https://m.media-amazon.com/images/I/71f-0m8-v7L._SL1500_.jpg"},
            {"name": "Lenovo Legion 5 Pro", "brand": "Lenovo", "price": 128000, "specs": "Ryzen 7, RTX 3060, QHD Display", "img": "https://m.media-amazon.com/images/I/61Xp0vHsh2L._SL1000_.jpg"},
            {"name": "Lenovo IdeaPad 3", "brand": "Lenovo", "price": 38000, "specs": "Intel Core i3, 8GB RAM, Student Edition", "img": "https://m.media-amazon.com/images/I/61q6x-Y6uyL._SL1500_.jpg"},
            {"name": "Acer Predator Helios", "brand": "Acer", "price": 110000, "specs": "i7 12th Gen, RTX 3060, RGB Keyboard", "img": "https://m.media-amazon.com/images/I/71-6Yf-H8vL._SL1500_.jpg"},
            {"name": "MSI Katana GF66", "brand": "MSI", "price": 82000, "specs": "i7 12th Gen, RTX 3050Ti, Gaming DNA", "img": "https://m.media-amazon.com/images/I/71m6k-8B8YL._SL1500_.jpg"},
            {"name": "Samsung Galaxy Book 3", "brand": "Samsung", "price": 74000, "specs": "Super AMOLED Display, i5 13th Gen", "img": "https://m.media-amazon.com/images/I/71WpB+Cid9L._SL1500_.jpg"},
            {"name": "Razer Blade 15", "brand": "Razer", "price": 245000, "specs": "i9, RTX 4080, CNC Aluminum Body", "img": "https://m.media-amazon.com/images/I/71S-S9I9-dL._SL1500_.jpg"},
            {"name": "Infinix Zero Book", "brand": "Infinix", "price": 52000, "specs": "i9 12th Gen, 16GB RAM, Budget King", "img": "https://m.media-amazon.com/images/I/61IunqD7x8L._SL1500_.jpg"}
        ]
            for item in laptops_data:
                p = Product(name=item['name'], brand=item['brand'], price=item['price'], specs=item['specs'], image_url=item['img'])
                db.session.add(p)
            db.session.commit()
            return "✅ Database Initialized! Tables created & Laptops added."
        
        return "ℹ️ Database already exists. No changes made."
    except Exception as e:
        db.session.rollback()
        return f"❌ Setup Failed: {e}"

@app.route('/')
def index():
    # 1. Database se saare laptops mangwao
    # 'Product' aapke model ka naam hona chahiye
    all_laptops = Product.query.all()
    
    # 2. Yahan dhyan do: 'laptops' naam se hi bhejiye 
    # kyunki aapne HTML mein 'for laptop in laptops' likha hai
    return render_template('index.html', laptops=all_laptops)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form.get('username')
        email = request.form.get('email')
        pwd = request.form.get('password')
        cpwd = request.form.get('confirm_password')

        if pwd != cpwd:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Email already registered!", "warning")
            return redirect(url_for('register'))

        hashed_pwd = generate_password_hash(pwd, method='pbkdf2:sha256')
        new_user = User(username=uname, email=email, password=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()        
        
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        # Ye brand ya name dono mein search karega
        results = Product.query.filter(
            (Product.name.like(f'%{query}%')) | 
            (Product.brand.like(f'%{query}%'))
        ).all()
    else:
        results = []
    
    return render_template('index.html', laptops=results, search_query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        from sqlalchemy import text
        from werkzeug.security import check_password_hash
        
        # User ko email se dhoondhein
        query = text("SELECT * FROM users WHERE email = :email")
        result = db.session.execute(query, {'email': email}).mappings().first()
        
        if result:
            is_valid = False
            # Check password (hashed or plain)
            try:
                if check_password_hash(result['password'], password):
                    is_valid = True
                elif result['password'] == password: # Fallback for plain text
                    is_valid = True
            except:
                if result['password'] == password:
                    is_valid = True

            if is_valid:
                session['user_id'] = result['id']
                session['user_name'] = result['username']
                
                # ⭐ SABSE ZAROORI LINE: Role ko session mein daalo
                session['role'] = result['role'] 
                
                flash("Login Successful!")
                print(f"DEBUG: Login Success. Role: {session['role']}, redirecting...")
                return redirect(url_for('index'))
            else:
                flash("Wrong Password!")
        else:
            flash("User not found!")
            
    return render_template('login.html')
@app.route('/logout')
def logout():
    session.clear() # Ye saara login data (user_id, name) delete kar dega
    flash("You have been logged out.")
    return redirect(url_for('login')) # Wapas login page par bhej dega


@app.route('/product/<int:laptop_id>')
def product_details(laptop_id):
    # Database se specific laptop ko ID ke zariye dhoondhein
    laptop = Product.query.get_or_404(laptop_id)
    # Related products dikhane ke liye usi brand ke aur laptops nikaalein
    related_laptops = Product.query.filter(Product.brand == laptop.brand, Product.id != laptop.id).limit(4).all()
    
    return render_template('product_details.html', laptop=laptop, related=related_laptops) 



@app.route('/add_to_cart/<int:laptop_id>')
def add_to_cart(laptop_id):
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect(url_for('login'))

    user_id = session['user_id']
    from sqlalchemy import text
    
    # URL se action check karo (Buy Now ke liye)
    action = request.args.get('action')

    try:
        # 1. Pehle check karo kya ye laptop pehle se cart mein hai?
        check_query = text("SELECT id FROM cart WHERE user_id = :u_id AND laptop_id = :l_id")
        existing_item = db.session.execute(check_query, {'u_id': user_id, 'l_id': laptop_id}).fetchone()

        if existing_item:
            # AGAR PEHLE SE HAI: Toh dobara add nahi karenge aur message dikhayenge
            # Buy Now par redirect karega, normal click par message dikhayega
            if action != 'buy':
                flash("This item is already in your cart!")
        else:
            # AGAR NAHI HAI: Toh insert karenge
            insert_query = text("INSERT INTO cart (user_id, laptop_id, quantity) VALUES (:u_id, :l_id, 1)")
            db.session.execute(insert_query, {'u_id': user_id, 'l_id': laptop_id})
            db.session.commit()
            
            # Sirf Add to Cart button ke liye success message dikhao
            if action != 'buy':
                flash("Item added to cart!")

        # 2. Navbar Count Update (Unique items)
        count_res = db.session.execute(text("SELECT COUNT(*) FROM cart WHERE user_id = :u"), {'u': user_id}).scalar()
        session['cart_total'] = int(count_res) if count_res else 0

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        flash("Something went wrong!")
        return redirect(url_for('index'))

    # --- FINAL REDIRECT LOGIC ---
    if action == 'buy':
        # Buy Now par seedha checkout (Bina pop-up ke)
        return redirect(url_for('checkout'))
    
    # Normal add to cart par wapas usi page par pop-up ke saath
    return redirect(request.referrer or url_for('index'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    from sqlalchemy import text
    
    # DHAYAN DEIN: Yahan 'laptop' table use karni hai, 'laptops' nahi
    query = text("""
        SELECT cart.id, laptop.name, laptop.price, laptop.image_url, cart.quantity, cart.laptop_id 
        FROM cart 
        JOIN laptop ON cart.laptop_id = laptop.id 
        WHERE cart.user_id = :u_id
    """)
    cart_items = db.session.execute(query, {'u_id': user_id}).mappings().all()
    
    # Total price calculate karna
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('cart.html', items=cart_items, total=total)

# Ye function navbar mein '3' ko badal kar sahi count dikhayega
@app.context_processor
def inject_cart_count():
    cart = session.get('cart', [])
    return dict(cart_count=len(cart))


@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return "Cart Cleared!"


@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    from sqlalchemy import text

    try:
        # Seedha Cart ID se delete karo taaki koi galti na ho
        db.session.execute(text("DELETE FROM cart WHERE id = :c_id AND user_id = :u_id"), 
                           {'c_id': cart_id, 'u_id': user_id})
        db.session.commit()

        # Naya count nikalo
        count_res = db.session.execute(text("SELECT COUNT(*) FROM cart WHERE user_id = :u"), {'u': user_id}).scalar()
        session['cart_total'] = int(count_res) if count_res else 0
        
        flash("Item removed successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Delete Error: {e}")

    return redirect(url_for('cart'))


@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    from sqlalchemy import text
    
    # 1. Cart check karein aur Total Price nikaalein (Summary ke liye)
    cart_query = text("""
        SELECT SUM(l.price * c.quantity) as total 
        FROM cart c 
        JOIN laptop l ON c.laptop_id = l.id 
        WHERE c.user_id = :u
    """)
    result = db.session.execute(cart_query, {'u': user_id}).fetchone()
    total_price = result.total if result.total else 0
    
    if total_price == 0:
        flash("Your cart is empty! Add something first.")
        return redirect(url_for('index'))
    
    # 2. User ki saved details nikaalo (Auto-fill ke liye)
    user_query = text("SELECT full_name, phone, address, city, pincode FROM users WHERE id = :u")
    user_data = db.session.execute(user_query, {'u': user_id}).fetchone()
    
    return render_template('checkout.html', user=user_data, total_price=total_price)
    
@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    from sqlalchemy import text
    
    # Form se naya data uthao
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    city = request.form.get('city')
    pincode = request.form.get('pincode')
    
    # Cart se final total verify karo
    cart_query = text("""
        SELECT SUM(l.price * c.quantity) as total 
        FROM cart c 
        JOIN laptop l ON c.laptop_id = l.id 
        WHERE c.user_id = :u
    """)
    result = db.session.execute(cart_query, {'u': user_id}).fetchone()
    total_amount = result.total if result.total else 0

    if total_amount == 0:
        flash("Order failed: Cart is empty!")
        return redirect(url_for('index'))

    try:
        # A. Sabse pehle User Table UPDATE karo (Agli baar ke liye details save ho gayi)
        update_user = text("""
            UPDATE users SET full_name=:n, phone=:p, address=:a, city=:c, pincode=:pin 
            WHERE id=:u
        """)
        db.session.execute(update_user, {
            'n': full_name, 'p': phone, 'a': address, 'c': city, 'pin': pincode, 'u': user_id
        })

        # B. Orders table mein entry dalo (status='Pending' aur payment='COD')
        order_query = text("""
            INSERT INTO orders (user_id, full_name, phone, address, city, pincode, total_amount, status, payment_mode)
            VALUES (:u, :n, :p, :a, :c, :pin, :total, 'Pending', 'COD')
        """)
        db.session.execute(order_query, {
            'u': user_id, 'n': full_name, 'p': phone, 
            'a': address, 'c': city, 'pin': pincode, 'total': total_amount
        })

        # C. Cart khali karo
        db.session.execute(text("DELETE FROM cart WHERE user_id = :u"), {'u': user_id})
        
        db.session.commit()
        session['cart_total'] = 0 
        
        flash("Order Placed Successfully via Cash on Delivery!")
        return redirect(url_for('my_orders'))

    except Exception as e:
        db.session.rollback()
        print(f"Checkout Error: {e}")
        flash("Kuch galat hua, dobara koshish karein!")
        return redirect(url_for('checkout'))
    

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    from sqlalchemy import text
    
    # Orders nikaalo - Latest order sabse upar
    query = text("SELECT * FROM orders WHERE user_id = :u ORDER BY order_date DESC")
    result = db.session.execute(query, {'u': user_id})
    
    # Ise list of dictionaries mein convert kar dete hain taaki HTML ko asani ho
    orders = result.mappings().all() 
    
    # Debugging: Terminal mein check karo ki data aa raha hai ya nahi
    print(f"DEBUG: Found {len(orders)} orders for user_id {user_id}")
    
    return render_template('my_orders.html', orders=orders)


from functools import wraps

# Decorator: Sirf Admin hi access kar paye
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash("Admin access required!")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    from sqlalchemy import text
    # Statistics nikaalo
    total_orders = db.session.execute(text("SELECT COUNT(*) FROM orders")).scalar()
    total_users = db.session.execute(text("SELECT COUNT(*) FROM users WHERE role='users'")).scalar()
    total_sales = db.session.execute(text("SELECT SUM(total_amount) FROM orders")).scalar() or 0
    
    # Latest Orders list
    orders = db.session.execute(text("SELECT * FROM orders ORDER BY order_date DESC LIMIT 10")).mappings().all()
    
    return render_template('admin/dashboard.html', 
                           total_orders=total_orders, 
                           total_users=total_users, 
                           total_sales=total_sales, 
                           orders=orders)

# Order Status Update karne ka route
@app.route('/admin/update_status/<int:order_id>', methods=['POST'])
@admin_required
def update_status(order_id):
    new_status = request.form.get('status')
    from sqlalchemy import text
    db.session.execute(text("UPDATE orders SET status = :s WHERE id = :id"), {'s': new_status, 'id': order_id})
    db.session.commit()
    flash(f"Order #{order_id} updated to {new_status}")
    return redirect(url_for('admin_dashboard'))    
# ------------------------------------------------------
# RUN THE APP
# ------------------------------------------------------

import os
from werkzeug.utils import secure_filename

# Folder jahan images save hongi
UPLOAD_FOLDER = 'static/uploads/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Folder agar nahi hai toh bana do
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        # 1. Data uthao aur agar khali ho toh default value de do
        brand = request.form.get('brand') or 'General'
        name = request.form.get('name') or 'New Laptop'
        price = request.form.get('price') or 0
        discount = request.form.get('discount') or 0
        desc = request.form.get('description') or 'No specifications provided.'
        file = request.files.get('image') # .get use karo taaki error na aaye
        
        img_path = "uploads/products/default.jpg" # Default image agar upload fail ho
        
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_path = f"uploads/products/{filename}"
            
        try:
            from sqlalchemy import text
            # Query wahi rahegi, bas data 'None' nahi jayega
            query = text("""
                INSERT INTO laptop (brand, name, price, discount, specs, image_url) 
                VALUES (:b, :n, :p, :disc, :s, :i)
            """)
            
            db.session.execute(query, {
                'b': brand,
                'n': name, 
                'p': price, 
                'disc': discount,
                's': desc, 
                'i': img_path
            })
            
            db.session.commit()
            flash("Laptop Added Successfully!")
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")
            flash(f"Error saving to database: {e}")
            
    return render_template('admin/add_product.html')
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0",debug=True, port=5001)