import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { ProjectEditForm } from "./ProjectEditForm";
import { ProjectSourcesPanel } from "./ProjectSourcesPanel";
import { useProjectQuery } from "./useProjectsQueries";

function formatStamp(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

export function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId ?? "";
  const projectQuery = useProjectQuery(projectId);

  if (!projectId) {
    return <ErrorState title="Projet invalide" message="Identifiant manquant." />;
  }

  if (projectQuery.isLoading) {
    return <Spinner label="Chargement du projet…" />;
  }

  if (projectQuery.isError) {
    return (
      <ErrorState
        title="Projet introuvable"
        message={projectQuery.error.message}
        onRetry={() => void projectQuery.refetch()}
      />
    );
  }

  const project = projectQuery.data;
  if (!project) {
    return <ErrorState title="Projet introuvable" message="Aucune donnée reçue." />;
  }

  return (
    <div className="project-detail">
      <p>
        <Link to="/projects">← Retour aux projets</Link>
      </p>
      <h2>{project.name}</h2>
      <p className="project-meta">
        Créé (UTC) : {formatStamp(project.created_at)} · Mis à jour (UTC) :{" "}
        {formatStamp(project.updated_at)}
      </p>
      <ProjectEditForm project={project} />
      <ProjectSourcesPanel projectId={project.id} />
    </div>
  );
}
