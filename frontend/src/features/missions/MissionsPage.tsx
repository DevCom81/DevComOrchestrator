import { Link } from "react-router-dom";

import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { MissionCreateForm } from "./MissionCreateForm";
import { statusLabel } from "./missionTypes";
import { useMissionsQuery } from "./useMissionsQueries";

export function MissionsPage() {
  const missions = useMissionsQuery();

  return (
    <div className="missions-page">
      <div className="missions-page__header">
        <h2>Missions</h2>
      </div>

      {missions.isLoading ? <Spinner label="Chargement des missions…" /> : null}
      {missions.isError ? (
        <ErrorState
          title="Impossible de charger les missions"
          message={missions.error.message}
          onRetry={() => void missions.refetch()}
        />
      ) : null}

      {!missions.isLoading && !missions.isError ? (
        missions.data?.items.length ? (
          <ul className="mission-list">
            {missions.data.items.map((mission) => (
              <li key={mission.id}>
                <Link to={`/missions/${mission.id}`}>
                  <div className="project-list__name">{mission.request_text}</div>
                  <p className="project-list__desc">{statusLabel(mission.status)}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="Aucune mission"
            message="Créez une mission depuis le formulaire ci-dessous ou le HQ."
          />
        )
      ) : null}

      <MissionCreateForm />
    </div>
  );
}
