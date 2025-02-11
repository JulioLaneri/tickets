from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
import qrcode
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
CORS(app, origins=[os.getenv("FRONTEND_URL")])

# Configuración de la base de datos MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    # "port": int(os.getenv("DB_PORT")),
}

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


# Crear la base de datos si no existe
def init_db():
    print(DB_CONFIG.get("port"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            event VARCHAR(255) NOT NULL,
            qr_code VARCHAR(255) UNIQUE NOT NULL,
            qr_url VARCHAR(500) NOT NULL,
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

    # Generar el código QR en memoria
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(qr_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar imagen temporalmente en memoria
    import io
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Subir a Cloudinary
    response = cloudinary.uploader.upload(img_buffer, folder="tickets_qr_codes")

    # Obtener URL del QR
    qr_url = response["secure_url"]

    # Guardar en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO tickets (name, email, event, qr_code, qr_url) VALUES (%s, %s, %s, %s, %s)",
            (name, email, event, qr_code, qr_url),
        )
        conn.commit()
        return jsonify({"message": "Ticket created", "qr": qr_code, "qr_url": qr_url})
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

    cursor.execute("SELECT id, name, email, event, status, qr_url FROM tickets WHERE qr_code = %s", (qr_code,))
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

    cursor.execute("SELECT id, name, email, event, qr_code, qr_url, status FROM tickets")
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(tickets)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)