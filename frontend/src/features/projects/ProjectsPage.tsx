import { Link } from "react-router-dom";

import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { ProjectCreateForm } from "./ProjectCreateForm";
import { useProjectsQuery } from "./useProjectsQueries";

export function ProjectsPage() {
  const projects = useProjectsQuery();

  return (
    <div className="projects-page">
      <div className="projects-page__header">
        <h2>Projets</h2>
      </div>

      {projects.isLoading ? <Spinner label="Chargement des projets…" /> : null}
      {projects.isError ? (
        <ErrorState
          title="Impossible de charger les projets"
          message={projects.error.message}
          onRetry={() => void projects.refetch()}
        />
      ) : null}

      {!projects.isLoading && !projects.isError ? (
        projects.data?.items.length ? (
          <ul className="project-list">
            {projects.data.items.map((project) => (
              <li key={project.id}>
                <Link to={`/projects/${project.id}`}>
                  <div className="project-list__name">{project.name}</div>
                  <p className="project-list__desc">{project.description}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="Aucun projet"
            message="Créez votre premier projet pour démarrer le Command Center."
          />
        )
      ) : null}

      <ProjectCreateForm />
    </div>
  );
}
