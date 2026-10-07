import { createBrowserRouter } from "react-router-dom";

import { HqPage } from "../features/hq/HqPage";
import { MissionDetailPage } from "../features/missions/MissionDetailPage";
import { MissionsPage } from "../features/missions/MissionsPage";
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
      { path: "missions", element: <MissionsPage /> },
      { path: "missions/:missionId", element: <MissionDetailPage /> },
    ],
  },
]);
