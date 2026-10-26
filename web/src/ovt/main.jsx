import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "../estilos.css";
import Ovt from "./Ovt.jsx";

createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <Ovt />
  </StrictMode>,
);
