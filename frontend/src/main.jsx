import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <p>Subscription Tracker</p>
  </StrictMode>,
);
