import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify"; // Importaciones
import "bootstrap/dist/css/bootstrap.min.css";
import "react-toastify/dist/ReactToastify.css"; // Estilos de react-toastify
import CreateTicket from "./components/CreateTicket";
import TicketsList from "./components/TicketsList";

function App() {
  return (
    <Router>
      <div className="App">
        <ToastContainer position="top-right" autoClose={3000} /> {/* Configuración del ToastContainer */}
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
          <div className="container-fluid">
            <Link to="/" className="navbar-brand">Ticket Manager</Link>
            <div className="navbar-nav">
              <Link to="/" className="nav-link">Crear Entrada</Link>
              <Link to="/tickets" className="nav-link">Ver Entradas</Link>
            </div>
          </div>
        </nav>
        <div className="container mt-4">
          <Routes>
            <Route path="/" element={<CreateTicket />} />
            <Route path="/tickets" element={<TicketsList />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;