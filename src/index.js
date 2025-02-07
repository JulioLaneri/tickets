import React from "react";
import { createRoot } from "react-dom/client"; // Importa createRoot
import App from "./App";

// Selecciona el contenedor raíz
const container = document.getElementById("root");

// Crea una raíz y renderiza la aplicación
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);