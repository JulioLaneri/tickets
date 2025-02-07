from flask import Flask, request, jsonify, send_from_directory
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
CORS(app, origins=["http://localhost:3000"])

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Configuración de MySQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )


# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        event VARCHAR(255) NOT NULL,
                        qr_code VARCHAR(255) UNIQUE NOT NULL,
                        qr_url TEXT NOT NULL,
                        status VARCHAR(50) DEFAULT 'active',
                        scanned_at DATETIME NULL)''')
    conn.commit()
    cursor.close()
    conn.close()


@app.route('/')
def home():
    return "¡Bienvenido al sistema de tickets!"


@app.route("/create_ticket", methods=["POST"])
def create_ticket():
    data = request.json
    name, email, event = data.get("name"), data.get("email"), data.get("event")
    if not all([name, email, event]):
        return jsonify({"error": "Missing data"}), 400

    qr_code = f"{name}_{email}_{event}"
    qr_filename = f"{qr_code}.png"
    qr_path = os.path.join("qrs", qr_filename)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)

    upload_result = cloudinary.uploader.upload(qr_path)
    qr_url = upload_result.get("secure_url")
    os.remove(qr_path)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO tickets (name, email, event, qr_code, qr_url) VALUES (%s, %s, %s, %s, %s)",
                       (name, email, event, qr_code, qr_url))
        conn.commit()
        return jsonify({"message": "Ticket created", "qr": qr_code, "qr_url": qr_url})
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Ticket already exists"}), 400
    finally:
        cursor.close()
        conn.close()


@app.route("/scan_ticket/<qr_code>", methods=["GET"])
def scan_ticket(qr_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, event, status FROM tickets WHERE qr_code = %s", (qr_code,))
    ticket = cursor.fetchone()

    if not ticket:
        return jsonify({"error": "Invalid ticket"}), 404

    if ticket[4] == "inactive":
        return jsonify({"error": "Ticket already used"}), 400

    cursor.execute("UPDATE tickets SET status = 'inactive', scanned_at = NOW() WHERE qr_code = %s", (qr_code,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Ticket validated",
        "ticket": {
            "id": ticket[0],
            "name": ticket[1],
            "email": ticket[2],
            "event": ticket[3],
            "status": "inactive"
        }
    })


@app.route("/get_tickets", methods=["GET"])
def get_tickets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, event, qr_code, qr_url, status FROM tickets")
    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify([
        {"id": row[0], "name": row[1], "email": row[2], "event": row[3], "qr_code": row[4], "qr_url": row[5],
         "status": row[6]}
        for row in tickets
    ])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
