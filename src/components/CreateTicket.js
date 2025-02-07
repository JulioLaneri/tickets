import React, { useState } from "react";
import { QRCodeCanvas } from "qrcode.react"; // Cambiado aquí
import { jsPDF } from "jspdf";
import ReactDOM from "react-dom/client";
import { toast } from "react-toastify";

function CreateTicket() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    event: "",
  });
  const [ticketCreated, setTicketCreated] = useState(false);
  const [qrCodeData, setQrCodeData] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const response = await fetch("http://localhost:5001/create_ticket", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(formData),
    });
  
    const data = await response.json();
    if (response.ok) {
      setTicketCreated(true);
      setQrCodeData(data.qr); // Guarda el código QR generado en el backend
      generatePDF(data.qr); // Genera y descarga el PDF
  
      // Limpiar los campos del formulario
      setFormData({
        name: "",
        email: "",
        event: "",
      });
  
      // Mostrar notificación
      toast.success("¡Entrada creada exitosamente!", {
        position: "top-right",
        autoClose: 3000,
      });
    } else {
      toast.error(data.error, {
        position: "top-right",
        autoClose: 3000,
      });
    }
  };

  const generatePDF = (qrData) => {
    const doc = new jsPDF();
    const margin = 10;
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
  
    // Agregar título
    doc.setFontSize(18);
    doc.text("Entrada para el Evento", margin, margin + 10);
  
    // Agregar detalles de la entrada
    doc.setFontSize(12);
    doc.text(`Nombre: ${formData.name}`, margin, margin + 30);
    doc.text(`Correo: ${formData.email}`, margin, margin + 40);
    doc.text(`Evento: ${formData.event}`, margin, margin + 50);
  
    // Generar el código QR en el PDF
    const qrSize = 100;
    const qrX = (pageWidth - qrSize) / 2;
    const qrY = margin + 60;
  
    // Crear un canvas temporal para el código QR
    const qrCodeCanvas = document.createElement("canvas");
    qrCodeCanvas.width = qrSize;
    qrCodeCanvas.height = qrSize;
  
    // Renderizar el código QR en el canvas
    const qrCode = (
      <QRCodeCanvas
        value={qrData}
        size={qrSize}
        level="H"
        canvas={qrCodeCanvas} // Usar el canvas creado
      />
    );
  
    // Renderizar el código QR en el canvas sin agregarlo al DOM
    const container = document.createElement("div");
    const root = ReactDOM.createRoot(container);
    root.render(qrCode);
  
    // Función para verificar si el canvas está listo
    const checkCanvasReady = () => {
      if (!isCanvasBlank(qrCodeCanvas)) {
        // El canvas está listo, capturar la imagen y agregarla al PDF
        const qrImage = qrCodeCanvas.toDataURL("image/png");
        doc.addImage(qrImage, "PNG", qrX, qrY, qrSize, qrSize);
  
        // Guardar el PDF con el nombre del comprador
        const fileName = `Entrada_${formData.name.replace(/ /g, "_")}.pdf`;
        doc.save(fileName);
  
        // Limpiar el contenedor
        root.unmount();
      } else {
        // El canvas no está listo, reintentar en 100 ms
        setTimeout(checkCanvasReady, 100);
      }
    };
  
    // Iniciar la verificación del canvas
    checkCanvasReady();
  };
  const isCanvasBlank = (canvas) => {
    const context = canvas.getContext("2d");
    const pixelBuffer = new Uint32Array(
      context.getImageData(0, 0, canvas.width, canvas.height).data.buffer
    );
    return !pixelBuffer.some((color) => color !== 0);
  };
  return (
    <div className="container mt-4">
      <h2>Crear Nueva Entrada</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label">Nombre</label>
          <input
            type="text"
            className="form-control"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Correo Electrónico</label>
          <input
            type="email"
            className="form-control"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="mb-3">
          <label className="form-label">Evento</label>
          <input
            type="text"
            className="form-control"
            name="event"
            value={formData.event}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Crear Entrada
        </button>
      </form>
      {ticketCreated && (
        <div className="mt-4">
          <p>¡Entrada creada exitosamente! Se ha descargado un PDF con tu código QR.</p>
        </div>
      )}
    </div>
  );
}

export default CreateTicket;