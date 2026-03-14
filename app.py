from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import pymysql
import hashlib
import os
import re
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
mail = Mail(app)

def get_db():
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='1234',
            database='irrigation_db',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        return conn
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        messages = {
            1045: "Mot de passe MySQL incorrect",
            1049: "Base 'irrigation_db' introuvable — crée-la dans phpMyAdmin",
            2003: "MySQL non démarré — lance WAMP/XAMPP",
        }
        print(f"[MySQL {code}] {messages.get(code, msg)}")
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def is_email(value):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value))

def normalize_phone(value):
    return re.sub(r'[\s\-().+]', '', value)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (
            request.form.get("email", "")
            or request.form.get("phone", "")
            or request.form.get("contact", "")
        ).strip()
        password = request.form.get("password", "")
        hashed = hashlib.sha256(password.encode()).hexdigest()

        if not identifier or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return render_template("login.html")

        conn = get_db()
        if not conn:
            flash("Impossible de se connecter à la base de données.", "error")
            return render_template("login.html")

        try:
            cursor = conn.cursor()

            if is_email(identifier):
                cursor.execute(
                    "SELECT * FROM users WHERE email = %s AND password = %s",
                    (identifier.lower(), hashed)
                )
            else:
                phone_clean = normalize_phone(identifier)
                cursor.execute(
                    "SELECT * FROM users WHERE telephone = %s AND password = %s",
                    (phone_clean, hashed)
                )

            user = cursor.fetchone()
        finally:
            conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_prenom'] = user['prenom']
            session['user_nom'] = user['nom']
            return redirect(url_for("dashboard"))
        else:
            flash("Identifiant ou mot de passe incorrect.", "error")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = {
        'prenom': session.get('user_prenom', ''),
        'nom': session.get('user_nom', ''),
        'email': session.get('user_email', ''),
    }
    return render_template("dashboard.html", user=user)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        prenom = request.form.get("prenom", "").strip()
        nom = request.form.get("nom", "").strip()
        dob = request.form.get("dob", "").strip()
        telephone = request.form.get("telephone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        cgu = request.form.get("cgu")

        if not all([prenom, nom, dob, telephone, email, password, confirm_password, cgu]):
            flash("Veuillez remplir tous les champs et accepter les CGU.", "error")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("signup"))

        dob_converted = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                dob_converted = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue

        if not dob_converted:
            flash("Format de date invalide.", "error")
            return redirect(url_for("signup"))

        conn = get_db()
        if not conn:
            flash("Impossible de se connecter à la base de données.", "error")
            return redirect(url_for("signup"))

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Un compte avec cet email existe déjà.", "error")
                return redirect(url_for("signup"))

            telephone_clean = normalize_phone(telephone)

            cursor.execute("SELECT id FROM users WHERE telephone = %s", (telephone_clean,))
            if cursor.fetchone():
                flash("Un compte avec ce numéro de téléphone existe déjà.", "error")
                return redirect(url_for("signup"))

            hashed = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                """INSERT INTO users (prenom, nom, dob, telephone, email, password)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (prenom, nom, dob_converted, telephone_clean, email, hashed)
            )
            conn.commit()
            print(f"[✓] Nouvel utilisateur : {email}")

        except Exception as e:
            flash(f"Erreur base de données : {str(e)}", "error")
            print(f"[!] Erreur MySQL : {e}")
            return redirect(url_for("signup"))
        finally:
            conn.close()

        try:
            msg = Message(
                subject="Bienvenue sur Irrigation Intelligente 🌿",
                recipients=[email],
                body=(
                    f"Bonjour {prenom},\n\n"
                    f"Votre compte a été créé avec succès.\n\n"
                    f"Cordialement,\nL'équipe Irrigation Intelligente"
                )
            )
            mail.send(msg)
            flash("Compte créé ✅ — E-mail de confirmation envoyé.", "success")
        except Exception as e:
            flash("Compte créé ✅ (email non envoyé)", "success")
            print(f"[!] Erreur email : {e}")

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password")
def forgot_password():
    return "Page de récupération (à implémenter)"

if __name__ == "__main__":
    app.run(debug=True)