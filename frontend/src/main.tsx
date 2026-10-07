import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./app/App";
import "./app/theme.css";
import "./app/shell.css";
import "./shared/ui/ui.css";
import "./features/hq/hq.css";
import "./features/projects/projects.css";
import "./features/missions/missions.css";
import "./features/tech/tech.css";


const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("root element missing");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
