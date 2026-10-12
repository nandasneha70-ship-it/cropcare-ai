import os
import sqlite3
import json
import uuid
import time
import cv2
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")

# Smart Crop AI - Disease Detection & Advisory Web Application
# Updated: Integrated robust Face & Blank/Non-leaf Image Safety Filters
load_dotenv(dotenv_path=ENV_FILE, override=True)

# 4. Startup check for GROQ_API_KEY
def startup_groq_check():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        print("\n" + "=" * 70)
        print("[STARTUP WARNING] GROQ_API_KEY is missing or empty!")
        print("    The Smart Farm Advisor chatbot will not function properly.")
        print(f"    Please configure GROQ_API_KEY in your .env file at:")
        print(f"    {ENV_FILE}")
        print("    Example: GROQ_API_KEY=gsk_your_groq_api_key_here")
        print("=" * 70 + "\n")
        return False
    masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
    print(f"[OK] [Groq Startup Check] GROQ_API_KEY loaded successfully ({masked})")
    return True

startup_groq_check()

DB_PATH = os.path.join(BASE_DIR, "users.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smartcrop123")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    )
    """)

    try:
        cursor.execute("SELECT profile_photo FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT DEFAULT 'static/images/default_profile.png'")

    try:
        cursor.execute("SELECT phone FROM users LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        image_path TEXT,
        disease_name TEXT,
        confidence REAL,
        solution_name TEXT,
        severity TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    try:
        cursor.execute("SELECT severity FROM history LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE history ADD COLUMN severity TEXT")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labor(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        name TEXT,
        role TEXT,
        wage REAL,
        contact TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        name TEXT,
        area REAL,
        coordinates TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financials(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        crop_name TEXT,
        labor_cost REAL,
        fertilizer_cost REAL,
        pesticide_cost REAL,
        other_cost REAL,
        expected_revenue REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inquiries(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'unread',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    default_users = [
        ("System Administrator", "admin@smartcrop.com", "admin123", "admin"),
        ("Ramesh Kumar (Farmer)", "farmer@smartcrop.com", "farmer123", "user")
    ]

    for fullname, email, password, role in default_users:
        try:
            if role == 'user':
                cursor.execute("INSERT INTO users (fullname, email, password) VALUES (?, ?, ?)", (fullname, email, password))
            else:
                cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)", (fullname, email, password, role))
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

# Auto-initialize database on application launch
init_db()

from src.predict import PlantDiseasePredictor
from src.translator import translator
from src.farmer_assistant import farmer_assistant, get_farming_response

# Load AI model
predictor = PlantDiseasePredictor()

# Load organic solutions database for AI Farmer Assistant
ORGANIC_DB_PATH = os.path.join(BASE_DIR, "data", "organic_solutions.json")
with open(ORGANIC_DB_PATH, "r", encoding="utf-8") as f:
    organic_db = json.load(f)



@app.before_request
def sync_lang():
    cookie_lang = request.cookies.get("farmer_lang")
    if cookie_lang and cookie_lang in ["en", "kn", "hi"]:
        session["lang"] = cookie_lang

@app.route("/set_lang", methods=["POST"])
def set_lang():
    data = request.get_json() or {}
    lang = data.get("lang", "en")
    if lang in ["en", "kn", "hi"]:
        session["lang"] = lang
        resp = make_response(jsonify({"status": "ok", "lang": lang}))
        resp.set_cookie("farmer_lang", lang, max_age=365*24*3600, path="/")
        return resp
    return jsonify({"status": "error", "message": "Invalid language"}), 400

@app.context_processor
def inject_user_profile():
    curr_lang = request.cookies.get("farmer_lang") or session.get("lang", "en")
    session["lang"] = curr_lang
    if "user_email" in session:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fullname, profile_photo, phone, role FROM users WHERE email=?", (session["user_email"],))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "current_user_fullname": row[0],
                "current_user_photo": row[1] or "static/images/default_profile.png",
                "current_user_phone": row[2] or "",
                "current_user_role": row[3] or "user",
                "session_lang": curr_lang
            }
    return {
        "current_user_fullname": None,
        "current_user_photo": "static/images/default_profile.png",
        "current_user_phone": "",
        "current_user_role": "guest",
        "session_lang": curr_lang
    }

# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- LOGIN ---------------- #

@app.route("/login")
def login():
    if "user" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register")
def register():
    if "user" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))
    return render_template("register.html")


# Register User
@app.route("/register_user", methods=["POST"])
def register_user():
    fullname = request.form["fullname"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users(fullname,email,password)
            VALUES(?,?,?)
        """, (fullname, email, password))
        conn.commit()
        error = None
    except sqlite3.IntegrityError:
        error = "Email already registered."
    finally:
        conn.close()

    if error:
        return render_template("register.html", error=error)

    return render_template("login.html", success="Registration successful! Please login.")

# ---------------- LOGIN USER ---------------- #

@app.route("/login_user", methods=["POST"])
def login_user():
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user"] = user[1]       # fullname
        session["user_email"] = user[2] # email
        session["role"] = user[4]       # role
        if user[4] == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    return render_template("login.html", error="Invalid Email or Password")

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("user_email", None)
    session.pop("role", None)
    return redirect(url_for("home"))


# ---------------- ADMIN PANEL ---------------- #

@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fetch system statistics
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM history")
    total_scans = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    admin_count = cursor.fetchone()[0]
    
    # 2. Fetch users and their scan counts
    cursor.execute("""
        SELECT u.id, u.fullname, u.email, u.role, COUNT(h.id) AS scan_count
        FROM users u
        LEFT JOIN history h ON u.email = h.user_email
        GROUP BY u.id
    """)
    users_data = cursor.fetchall()
    
    # Format user data list
    users_list = []
    for row in users_data:
        users_list.append({
            "id": row[0],
            "fullname": row[1],
            "email": row[2],
            "role": row[3],
            "scan_count": row[4]
        })
        
    # 3. Fetch global recent scans
    cursor.execute("""
        SELECT user_email, disease_name, confidence, timestamp
        FROM history
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    recent_scans_data = cursor.fetchall()
    
    # 4. Fetch Support Inquiries
    cursor.execute("SELECT COUNT(*) FROM inquiries")
    inquiry_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, name, email, subject, message, status, timestamp
        FROM inquiries
        ORDER BY timestamp DESC
    """)
    inquiries_data = cursor.fetchall()

    conn.close()
    
    recent_scans = []
    for row in recent_scans_data:
        recent_scans.append({
            "user_email": row[0],
            "disease_name": row[1],
            "confidence": row[2],
            "timestamp": row[3]
        })

    inquiries_list = []
    for row in inquiries_data:
        inquiries_list.append({
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "subject": row[3],
            "message": row[4],
            "status": row[5],
            "timestamp": row[6]
        })

    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        total_scans=total_scans,
        admin_count=admin_count,
        inquiry_count=inquiry_count,
        users=users_list,
        recent_scans=recent_scans,
        inquiries=inquiries_list,
        username=session["user"]
    )


@app.route("/admin/inquiry/<int:inquiry_id>/delete", methods=["POST"])
def delete_inquiry(inquiry_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inquiries WHERE id=?", (inquiry_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/toggle_role", methods=["POST"])
def toggle_role(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user to ensure we don't toggle ourselves
    cursor.execute("SELECT email, role FROM users WHERE id=?", (user_id,))
    target_user = cursor.fetchone()
    
    if target_user:
        target_email, target_role = target_user
        if target_email == session["user_email"]:
            # Can't toggle yourself!
            conn.close()
            return redirect(url_for("admin_dashboard"))
            
        new_role = "admin" if target_role == "user" else "user"
        cursor.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        conn.commit()
        
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user to ensure we don't delete ourselves
    cursor.execute("SELECT email FROM users WHERE id=?", (user_id,))
    target_user = cursor.fetchone()
    
    if target_user:
        target_email = target_user[0]
        if target_email == session["user_email"]:
            # Can't delete yourself!
            conn.close()
            return redirect(url_for("admin_dashboard"))
            
        # Delete user
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        # Delete user's history
        cursor.execute("DELETE FROM history WHERE user_email=?", (target_email,))
        conn.commit()
        
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/user/<email>/history")
def admin_user_history(email):
    if "user" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verify user exists
    cursor.execute("SELECT fullname FROM users WHERE email=?", (email,))
    target_user = cursor.fetchone()
    
    if not target_user:
        conn.close()
        return redirect(url_for("admin_dashboard"))
        
    fullname = target_user[0]
    
    # Fetch history data
    cursor.execute(
        "SELECT image_path, disease_name, confidence, solution_name, timestamp FROM history WHERE user_email=? ORDER BY timestamp DESC",
        (email,)
    )
    history_data = cursor.fetchall()
    conn.close()

    formatted_history = []
    for row in history_data:
        formatted_history.append({
            "image_path": row[0],
            "disease_name": row[1],
            "confidence": row[2],
            "solution_name": row[3],
            "timestamp": row[4]
        })

    return render_template(
        "admin_user_history.html",
        target_email=email,
        target_name=fullname,
        history=formatted_history
    )

# ---------------- DETECT ---------------- #

@app.route("/detect")
def detect():
    current_lang = request.cookies.get("farmer_lang") or session.get("lang", "en")
    session["lang"] = current_lang
    return render_template("detect.html", current_lang=current_lang)


# ---------------- GOVERNMENT SCHEMES ---------------- #

@app.route("/schemes")
def schemes():
    return render_template("schemes.html")


# ---------------- DASHBOARD ---------------- #
# ---------------- DASHBOARD ---------------- #
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch profile info for this user
    cursor.execute("SELECT fullname, email, role FROM users WHERE email=?", (email,))
    profile_row = cursor.fetchone()
    profile = {
        "fullname": profile_row[0],
        "email": profile_row[1],
        "role": profile_row[2]
    } if profile_row else {"fullname": session.get("user"), "email": email, "role": session.get("role")}

    # Fetch total scans for this user
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_email=?", (email,))
    scan_count = cursor.fetchone()[0]
    
    # Fetch healthy scans
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_email=? AND disease_name LIKE '%healthy%'", (email,))
    healthy_count = cursor.fetchone()[0]

    # Fetch diseased scans
    cursor.execute("SELECT COUNT(*) FROM history WHERE user_email=? AND disease_name NOT LIKE '%healthy%'", (email,))
    disease_count = cursor.fetchone()[0]
    
    # Fetch recent history
    cursor.execute("SELECT disease_name, confidence, timestamp FROM history WHERE user_email=? ORDER BY timestamp DESC LIMIT 5", (email,))
    recent_scans = cursor.fetchall()

    # Fetch tasks
    cursor.execute("SELECT id, description, due_date, status FROM tasks WHERE user_email=? ORDER BY due_date ASC", (email,))
    tasks_data = cursor.fetchall()
    tasks = [{"id": r[0], "description": r[1], "due_date": r[2], "status": r[3]} for r in tasks_data]

    # Fetch labor
    cursor.execute("SELECT id, name, role, wage, contact FROM labor WHERE user_email=?", (email,))
    labor_data = cursor.fetchall()
    labor = [{"id": r[0], "name": r[1], "role": r[2], "wage": r[3], "contact": r[4]} for r in labor_data]

    # Fetch plots
    cursor.execute("SELECT id, name, area, coordinates FROM plots WHERE user_email=?", (email,))
    plots_data = cursor.fetchall()
    plots = [{"id": r[0], "name": r[1], "area": r[2], "coordinates": r[3]} for r in plots_data]

    # Fetch financials
    cursor.execute("SELECT id, crop_name, labor_cost, fertilizer_cost, pesticide_cost, other_cost, expected_revenue, timestamp FROM financials WHERE user_email=? ORDER BY timestamp DESC", (email,))
    financials_data = cursor.fetchall()
    financials = []
    total_cost = 0.0
    total_revenue = 0.0
    for r in financials_data:
        cost = (r[2] or 0.0) + (r[3] or 0.0) + (r[4] or 0.0) + (r[5] or 0.0)
        rev = r[6] or 0.0
        net = rev - cost
        total_cost += cost
        total_revenue += rev
        financials.append({
            "id": r[0],
            "crop_name": r[1],
            "labor_cost": r[2] or 0.0,
            "fertilizer_cost": r[3] or 0.0,
            "pesticide_cost": r[4] or 0.0,
            "other_cost": r[5] or 0.0,
            "total_cost": cost,
            "expected_revenue": rev,
            "net_profit": net,
            "timestamp": r[7].split()[0] if r[7] else ""
        })
    expected_profit = total_revenue - total_cost

    conn.close()

    return render_template(
        "dashboard.html",
        username=session["user"],
        profile=profile,
        scan_count=scan_count,
        healthy_count=healthy_count,
        disease_count=disease_count,
        recent_scans=recent_scans,
        tasks=tasks,
        labor=labor,
        plots=plots,
        financials=financials,
        total_cost=round(total_cost, 2),
        total_revenue=round(total_revenue, 2),
        expected_profit=round(expected_profit, 2)
    )

# ---------------- PROFILE ---------------- #
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    
    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT fullname, email, profile_photo, phone FROM users WHERE email=?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    user_info = {}
    if row:
        user_info = {
            "fullname": row[0],
            "email": row[1],
            "profile_photo": row[2] or "static/images/default_profile.png",
            "phone": row[3] or ""
        }
    else:
        user_info = {
            "fullname": session.get("user"),
            "email": email,
            "profile_photo": "static/images/default_profile.png",
            "phone": ""
        }
        
    return render_template("profile.html", user_info=user_info)


@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user_email"]
    fullname = request.form.get("fullname", "").strip()
    phone = request.form.get("phone", "").strip()
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    error = None
    success = None
    
    # Process profile photo upload
    profile_photo = request.files.get("profile_photo")
    photo_path = None
    if profile_photo and profile_photo.filename != "":
        filename = secure_filename(profile_photo.filename)
        profiles_dir = os.path.join(app.config["UPLOAD_FOLDER"], "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        filepath = os.path.join(profiles_dir, filename)
        profile_photo.save(filepath)
        photo_path = f"static/uploads/profiles/{filename}"

    if new_password:
        if new_password != confirm_password:
            error = "New password and confirmation do not match."
        else:
            if photo_path:
                cursor.execute(
                    "UPDATE users SET fullname=?, phone=?, password=?, profile_photo=? WHERE email=?",
                    (fullname, phone, new_password, photo_path, email)
                )
            else:
                cursor.execute(
                    "UPDATE users SET fullname=?, phone=?, password=? WHERE email=?",
                    (fullname, phone, new_password, email)
                )
    else:
        if photo_path:
            cursor.execute(
                "UPDATE users SET fullname=?, phone=?, profile_photo=? WHERE email=?",
                (fullname, phone, photo_path, email)
            )
        else:
            cursor.execute(
                "UPDATE users SET fullname=?, phone=? WHERE email=?",
                (fullname, phone, email)
            )

    if not error:
        conn.commit()
        session["user"] = fullname  # keep session display name in sync
        success = "Profile updated successfully!"

    conn.close()

    if error:
        return render_template("profile.html", error=error, user_info={
            "fullname": fullname,
            "email": email,
            "phone": phone,
            "profile_photo": "static/images/default_profile.png"
        })

    # Fetch fresh info to render profile template with success message
    user_info = {
        "fullname": fullname,
        "email": email,
        "phone": phone,
        "profile_photo": photo_path or "static/images/default_profile.png"
    }
    
    # Fetch the actual photo from DB if not uploaded
    if not photo_path:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT profile_photo FROM users WHERE email=?", (email,))
        row = cursor.fetchone()
        conn.close()
        user_info["profile_photo"] = (row[0] if row else None) or "static/images/default_profile.png"

    return render_template("profile.html", success=success, user_info=user_info)


# ---------------- CROP GUIDE ---------------- #
@app.route("/crop_guide")
def crop_guide():
    return render_template("crop_guide.html")


# ---------------- AI FARMING ASSISTANT ---------------- #
@app.route("/ai_assistant")
def ai_assistant():
    current_lang = request.cookies.get("farmer_lang") or session.get("lang", "en")
    session["lang"] = current_lang
    last_pred = session.get("last_prediction")
    active_scan = None
    if last_pred:
        loc = translator.localize_result(last_pred, current_lang)
        active_scan = {
            "disease_name": loc["display_label"],
            "crop_name": loc.get("crop_name", ""),
            "confidence": f"{float(last_pred.get('confidence', 0.0)) * 100:.1f}%",
            "is_low_conf": float(last_pred.get("confidence", 0.0)) < 0.65
        }
    return render_template("ai_assistant.html", current_lang=current_lang, active_scan=active_scan)


# ---------------- LABOR CRUD ---------------- #
@app.route("/add_labor", methods=["POST"])
def add_labor():
    if "user" not in session:
        return redirect(url_for("login"))
    name = request.form.get("name")
    role = request.form.get("role")
    wage = float(request.form.get("wage") or 0.0)
    contact = request.form.get("contact")
    email = session["user_email"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO labor (user_email, name, role, wage, contact)
        VALUES (?, ?, ?, ?, ?)
    """, (email, name, role, wage, contact))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-scheduler")

@app.route("/delete_labor/<int:labor_id>", methods=["POST", "GET"])
def delete_labor(labor_id):
    if "user" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM labor WHERE id=? AND user_email=?", (labor_id, email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-scheduler")

# ---------------- TASK CRUD ---------------- #
@app.route("/add_task", methods=["POST"])
def add_task():
    if "user" not in session:
        return redirect(url_for("login"))
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    email = session["user_email"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (user_email, description, due_date)
        VALUES (?, ?, ?)
    """, (email, description, due_date))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-scheduler")

@app.route("/update_task_status/<int:task_id>", methods=["POST"])
def update_task_status(task_id):
    if "user" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]
    status = request.form.get("status", "pending")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status=? WHERE id=? AND user_email=?", (status, task_id, email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-scheduler")

@app.route("/delete_task/<int:task_id>", methods=["POST", "GET"])
def delete_task(task_id):
    if "user" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=? AND user_email=?", (task_id, email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-scheduler")

# ---------------- PLOT CRUD ---------------- #
@app.route("/add_plot", methods=["POST"])
def add_plot():
    if "user" not in session:
        return redirect(url_for("login"))
    name = request.form.get("name")
    area = float(request.form.get("area") or 0.0)
    coordinates = request.form.get("coordinates")
    email = session["user_email"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plots (user_email, name, area, coordinates)
        VALUES (?, ?, ?, ?)
    """, (email, name, area, coordinates))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-gps")

@app.route("/delete_plot/<int:plot_id>", methods=["POST", "GET"])
def delete_plot(plot_id):
    if "user" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plots WHERE id=? AND user_email=?", (plot_id, email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-gps")

# ---------------- FINANCIAL CRUD ---------------- #
@app.route("/add_financial", methods=["POST"])
def add_financial():
    if "user" not in session:
        return redirect(url_for("login"))
    crop_name = request.form.get("crop_name")
    labor_cost = float(request.form.get("labor_cost") or 0.0)
    fertilizer_cost = float(request.form.get("fertilizer_cost") or 0.0)
    pesticide_cost = float(request.form.get("pesticide_cost") or 0.0)
    other_cost = float(request.form.get("other_cost") or 0.0)
    expected_revenue = float(request.form.get("expected_revenue") or 0.0)
    email = session["user_email"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO financials (user_email, crop_name, labor_cost, fertilizer_cost, pesticide_cost, other_cost, expected_revenue)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (email, crop_name, labor_cost, fertilizer_cost, pesticide_cost, other_cost, expected_revenue))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-finance")

@app.route("/delete_financial/<int:financial_id>", methods=["POST", "GET"])
def delete_financial(financial_id):
    if "user" not in session:
        return redirect(url_for("login"))
    email = session["user_email"]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM financials WHERE id=? AND user_email=?", (financial_id, email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard") + "#tab-finance")

# ---------------- CHATBOT API ---------------- #
@app.route("/chat_api", methods=["POST"])
def chat_api():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"response": "Please enter a message.", "lang": "en"})

    lang = data.get("lang") or request.cookies.get("farmer_lang") or session.get("lang") or "en"
    session["lang"] = lang
    session_id = data.get("session_id") or session.get("chat_session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        session["chat_session_id"] = session_id

    # Resolve active scan from frontend or session
    active_scan = data.get("activeScan") or data.get("active_scan")
    if not active_scan:
        last_pred = session.get("last_prediction")
        if last_pred:
            label = last_pred.get("label", "").replace("___", " - ").replace("_", " ")
            conf = float(last_pred.get("confidence", 0.0)) * 100
            active_scan = f"{label} ({conf:.0f}%)"
        else:
            active_scan = "Tomato - Late blight 43%"

    # Resolve chat history from frontend
    chat_history = data.get("chat_history") or data.get("chatHistory") or []

    try:
        response_text = get_farming_response(
            user_message=query,
            chat_history=chat_history,
            active_scan=active_scan
        )
    except Exception as e:
        print(f"[Chat API Error] Exception during get_farming_response: {e}")
        response_text = f"AI service error: {e}"

    final_lang = lang
    if any('\u0C80' <= c <= '\u0CFF' for c in response_text) or any('\u0C80' <= c <= '\u0CFF' for c in query):
        final_lang = "kn"
    elif any('\u0900' <= c <= '\u097F' for c in response_text) or any('\u0900' <= c <= '\u097F' for c in query):
        final_lang = "hi"
    elif not any('\u0C80' <= c <= '\u0CFF' for c in query) and not any('\u0900' <= c <= '\u097F' for c in query) and lang == "en":
        final_lang = "en"

    session["lang"] = final_lang
    resp = make_response(jsonify({
        "response": response_text,
        "session_id": session_id,
        "lang": final_lang
    }))
    resp.set_cookie("farmer_lang", final_lang, max_age=365*24*3600, path="/")
    return resp

@app.route("/reset_chat", methods=["POST"])
def reset_chat():
    sid = session.get("chat_session_id")
    if sid:
        farmer_assistant.clear_context(sid)
    return {"status": "ok"}


# ---------------- HISTORY ---------------- #

@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT image_path, disease_name, confidence, solution_name, timestamp FROM history WHERE user_email=? ORDER BY timestamp DESC",
        (session["user_email"],)
    )
    history_data = cursor.fetchall()
    conn.close()

    # Format history data for rendering
    formatted_history = []
    for row in history_data:
        formatted_history.append({
            "image_path": row[0],
            "disease_name": row[1],
            "confidence": row[2],
            "solution_name": row[3],
            "timestamp": row[4]
        })

    return render_template("history.html", history=formatted_history)


# ---------------- ABOUT ---------------- #

@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- CONTACT ---------------- #

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return render_template("contact.html", error="Please fill in all required fields.")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inquiries (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        """, (name, email, subject, message))
        conn.commit()
        conn.close()

        return render_template("contact.html", success="Message sent successfully! Our agricultural support desk has received your inquiry.")

    return render_template("contact.html")


# ---------------- AI PREDICTION ---------------- #

@app.route("/predict", methods=["POST"])
def predict():
    lang = request.form.get("lang") or request.cookies.get("farmer_lang") or session.get("lang") or "en"
    if lang not in ["en", "kn", "hi"]:
        lang = "en"
    session["lang"] = lang

    if "image" not in request.files:
        return render_template("detect.html", error="No image uploaded. Please choose a plant leaf photo.", current_lang=lang)

    file = request.files["image"]

    if file.filename == "":
        return render_template("detect.html", error="Please select an image file to analyze.", current_lang=lang)

    crop = request.form.get("crop", "auto")

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    rel_image_path = f"static/uploads/{filename}"

    try:
        raw_result = predictor.predict(filepath, crop=crop)
    except Exception as e:
        return render_template("detect.html", error=f"Error analyzing image: {str(e)}", current_lang=lang)

    if raw_result.get("is_invalid"):
        error_msg = raw_result.get("error_message") or raw_result.get("error") or "Invalid image. Please upload a clear photo of a crop leaf."
        if lang in ["kn", "hi"]:
            error_msg = translator.translate_dynamic(error_msg, lang)
        return render_template("detect.html", error=error_msg, current_lang=lang)
    # Generate complete multilingual bundle for en, kn, hi
    multilingual_bundle = translator.get_multilingual_bundle(raw_result)
    result = multilingual_bundle.get(lang, multilingual_bundle["en"])

    # Save to last_prediction in session for AI Farmer Assistant
    session["last_prediction"] = {
        "label": raw_result["label"],
        "confidence": float(raw_result["confidence"]),
        "severity": raw_result.get("severity", "Moderate"),
        "severity_pct": float(raw_result.get("severity_pct", 0.0)),
        "solution": raw_result.get("solution", {}),
        "image_path": rel_image_path,
        "timestamp": time.time()
    }

    # Save to history if user is logged in
    if "user_email" in session:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sol_name = raw_result["solution"]["solution_name"] if (raw_result.get("solution") and "solution_name" in raw_result["solution"]) else "Organic Remedy"
        cursor.execute("""
            INSERT INTO history (user_email, image_path, disease_name, confidence, solution_name, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_email"],
            rel_image_path,
            raw_result["label"],
            raw_result["confidence"],
            sol_name,
            raw_result.get("severity", "N/A")
        ))
        conn.commit()
        conn.close()

    rendered = render_template(
        "result.html",
        result=result,
        multilingual_bundle=multilingual_bundle,
        current_lang=lang,
        image_url="/" + rel_image_path
    )
    resp = make_response(rendered)
    resp.set_cookie("farmer_lang", lang, max_age=365*24*3600, path="/")
    return resp


# ---------------- RUN APP ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "True").lower() in ["true", "1", "yes"]
    app.run(host="0.0.0.0", port=port, debug=debug_mode)