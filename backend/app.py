from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import os
import qrcode
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configurar CORS
CORS(app, origins=["http://localhost:5173"])


# Configuración de la base de datos MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT"))
}


# Función para conectar con la base de datos
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


# Crear la base de datos si no existe
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        event VARCHAR(255) NOT NULL,
                        qr_code VARCHAR(255) UNIQUE NOT NULL,
                        status ENUM('active', 'inactive') DEFAULT 'active',
                        scanned_at DATETIME DEFAULT NULL)''')

    conn.commit()
    cursor.close()
    conn.close()


@app.route('/')
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
    qr_filename = f"qrs/{qr_code}.png"

    # Generar la imagen del código QR
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(qr_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_filename)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO tickets (name, email, event, qr_code) VALUES (%s, %s, %s, %s)",
                       (name, email, event, qr_code))
        conn.commit()
        return jsonify({"message": "Ticket created", "qr": qr_code, "qr_image": qr_filename})
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

    cursor.execute("SELECT id, name, email, event, status FROM tickets WHERE qr_code = %s", (qr_code,))
    ticket = cursor.fetchone()

    if not ticket:
        return jsonify({"error": "Invalid ticket"}), 404

    if ticket["status"] == "inactive":
        return jsonify({"error": "Ticket already used"}), 400

    # Marcar el ticket como usado
    cursor.execute("UPDATE tickets SET status = 'inactive', scanned_at = NOW() WHERE qr_code = %s", (qr_code,))
    conn.commit()

    ticket["status"] = "inactive"

    cursor.close()
    conn.close()

    return jsonify({"message": "Ticket validated", "ticket": ticket})


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


# Ruta para servir imágenes QR
@app.route("/qrs/<filename>")
def get_qr_image(filename):
    return send_from_directory("qrs", filename)


if __name__ == "__main__":
    if not os.path.exists("qrs"):
        os.makedirs("qrs")
    init_db()
    app.run(debug=True, port=5001)
