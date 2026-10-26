import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "../estilos.css";
import Consola from "./Consola.jsx";

createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <Consola />
  </StrictMode>,
);
