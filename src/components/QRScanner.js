import React, { useEffect } from "react";
import { Html5QrcodeScanner } from "html5-qrcode";

const QRScanner = ({ onScan }) => {
  useEffect(() => {
    const scanner = new Html5QrcodeScanner("qr-scanner", {
      qrbox: {
        width: 250,
        height: 250,
      },
      fps: 5,
    });

    scanner.render((qrCodeData) => {
      onScan(qrCodeData); // Llamar a la función onScan con el código QR escaneado
      scanner.clear(); // Detener el escáner después de leer un código
    });

    return () => {
      scanner.clear(); // Limpiar el escáner cuando el componente se desmonte
    };
  }, [onScan]);

  return <div id="qr-scanner" style={{ width: "100%", maxWidth: "500px" }}></div>;
};

export default QRScanner;