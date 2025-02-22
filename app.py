from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import qrcode
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"])

# Configuración de la base de datos MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT")),
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Crear la base de datos si no existe
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            event VARCHAR(255) NOT NULL,
            qr_code VARCHAR(255) UNIQUE NOT NULL,
            status ENUM('active', 'inactive') DEFAULT 'active',
            scanned_at DATETIME DEFAULT NULL
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/")
def home():
    return "¡Bienvenido al sistema de tickets!"

# Ruta para crear un ticket
@app.route("/create_ticket", methods=["POST"])
def create_ticket():
    data = request.json
    name, email, event = data.get("name"), data.get("email"), data.get("event")

    if not all([name, email, event]):
        return jsonify({"error": "Missing data"}), 400

    qr_code = f"{name}_{email}_{event}"

    # Guardar en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO tickets (name, email, event, qr_code) VALUES (%s, %s, %s, %s)",
            (name, email, event, qr_code),
        )
        conn.commit()
        return jsonify({"message": "Ticket created", "qr": qr_code})
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Ticket already exists"}), 400
    finally:
        cursor.close()
        conn.close()

# Ruta para escanear un ticket

@app.route("/scan_ticket/<qr_code>", methods=["GET"])
def scan_ticket(qr_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email, event, status, scanned_at FROM tickets WHERE qr_code = %s", (qr_code,))
    ticket = cursor.fetchone()

    if not ticket:
        return jsonify({"error": "Código QR inválido", "color": "red"}), 404

    if ticket["status"] == "inactive":
        scanned_at = ticket["scanned_at"].strftime("%d/%m/%Y %H:%M:%S") if ticket["scanned_at"] else "Desconocido"
        return jsonify({
            "error": "Ticket ya utilizado",
            "color": "red",
            "scanned_at": scanned_at
        }), 400

    # Marcar el ticket como usado con fecha y hora de escaneo
    scanned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE tickets SET status = 'inactive', scanned_at = %s WHERE qr_code = %s", (scanned_at, qr_code))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": f"Bienvenido, {ticket['name']}! Disfruta el evento {ticket['event']}",
        "color": "green",
        "scanned_at": scanned_at
    })

# Ruta para obtener todos los tickets
@app.route("/get_tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email, event, qr_code, status FROM tickets")
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(tickets)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)