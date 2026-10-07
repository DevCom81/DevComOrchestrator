import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { useAgentsQuery } from "../hq/useAgentsQuery";
import { ClarificationForm } from "./ClarificationForm";
import { MissionTaskCard } from "./MissionTaskCard";
import { statusClassName, statusLabel } from "./missionTypes";
import { useMissionQuery } from "./useMissionsQueries";

export function MissionDetailPage() {
  const params = useParams();
  const missionId = params.missionId ?? "";
  const missionQuery = useMissionQuery(missionId);
  const agents = useAgentsQuery();

  if (!missionId) {
    return <ErrorState title="Mission invalide" message="Identifiant manquant." />;
  }
  if (missionQuery.isLoading) {
    return <Spinner label="Chargement de la mission…" />;
  }
  if (missionQuery.isError) {
    return (
      <ErrorState
        title="Mission introuvable"
        message={missionQuery.error.message}
        onRetry={() => void missionQuery.refetch()}
      />
    );
  }

  const mission = missionQuery.data;
  if (!mission) {
    return <ErrorState title="Mission introuvable" message="Aucune donnée." />;
  }

  const names = new Map(
    (agents.data?.items ?? []).map((agent) => [agent.id, agent.display_name]),
  );

  return (
    <div className="mission-detail">
      <p>
        <Link to="/missions">← Missions</Link>
      </p>
      <div className="mission-detail__header">
        <h2>Mission</h2>
        <span className={statusClassName(mission.status)}>
          {statusLabel(mission.status)}
        </span>
      </div>
      <p className="muted">{mission.request_text}</p>
      {mission.routing ? (
        <div className="mission-panel">
          <p className="demo-disclaimer">{mission.routing.disclaimer}</p>
          <p>
            <strong>Explication :</strong> {mission.routing.rationale}
          </p>
          <p className="muted">
            Règles {mission.routing.rule_ids.join(", ")} · registry v
            {mission.routing.capability_registry_version} · policy v
            {mission.routing.permission_policy_version} · dispatch v
            {mission.routing.dispatch_rules_version}
          </p>
        </div>
      ) : null}

      {mission.status === "routed" ? (
        <p className="muted">
          Routage consultable uniquement — aucun travail IA n&apos;a été exécuté.
        </p>
      ) : null}

      {mission.authorization_block ? (
        <div className="auth-block" role="status">
          <h3>{mission.authorization_block.message}</h3>
          <p>{mission.authorization_block.rationale}</p>
          <p className="muted">
            Aucune approbation ni exécution n&apos;est disponible dans ce lot.
          </p>
        </div>
      ) : null}

      {mission.status === "awaiting_clarification" &&
      mission.clarification_token ? (
        <ClarificationForm
          missionId={mission.id}
          token={mission.clarification_token}
          questions={mission.clarification_questions}
        />
      ) : null}

      {mission.tasks.length > 0 ? (
        <section aria-label="Agents retenus">
          <h3>Agents retenus</h3>
          <div className="task-grid">
            {mission.tasks.map((task) => (
              <MissionTaskCard
                key={task.id}
                task={task}
                agentName={names.get(task.agent_id) ?? task.agent_id}
              />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
