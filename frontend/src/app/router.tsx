import { createBrowserRouter } from "react-router-dom";

import { HqPage } from "../features/hq/HqPage";
import { ProjectDetailPage } from "../features/projects/ProjectDetailPage";
import { ProjectsPage } from "../features/projects/ProjectsPage";
import { AppShell } from "./layout/AppShell";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <HqPage /> },
      { path: "projects", element: <ProjectsPage /> },
      { path: "projects/:projectId", element: <ProjectDetailPage /> },
    ],
  },
]);
