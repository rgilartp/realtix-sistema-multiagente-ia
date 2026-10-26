import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "../estilos.css";
import Widget from "./Widget.jsx";

createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <Widget />
  </StrictMode>,
);
