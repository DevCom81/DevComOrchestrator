import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { useAgentsQuery } from "../hq/useAgentsQuery";
import { AdrPanel } from "./AdrPanel";
import { AnalysesPanel } from "./AnalysesPanel";
import { DecisionPanel } from "./DecisionPanel";
import { ProposalsPanel } from "./ProposalsPanel";
import { RealLaunchPanel } from "./RealLaunchPanel";
import { RealStepsPanel } from "./RealStepsPanel";
import { ReviewStatusBanner } from "./ReviewStatusBanner";
import { ScenarioSelectPanel } from "./ScenarioSelectPanel";
import { techStatusLabel } from "./techTypes";
import { useTechReviewQuery } from "./useTechQueries";

export function TechReviewDetailPage() {
  const params = useParams();
  const reviewId = params.reviewId ?? "";
  const reviewQuery = useTechReviewQuery(reviewId, true);
  const agents = useAgentsQuery();
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);

  if (!reviewId) {
    return <ErrorState title="Revue invalide" message="Identifiant manquant." />;
  }
  if (reviewQuery.isLoading) {
    return <Spinner label="Chargement de la revue TECH…" />;
  }
  if (reviewQuery.isError) {
    return (
      <ErrorState
        title="Revue introuvable"
        message={reviewQuery.error.message}
        onRetry={() => void reviewQuery.refetch()}
      />
    );
  }
  const review = reviewQuery.data;
  if (!review) {
    return <ErrorState title="Revue introuvable" message="Aucune donnée." />;
  }

  const names = new Map(
    (agents.data?.items ?? []).map((agent) => [agent.id, agent.display_name]),
  );
  const decidedId = review.decision?.proposal_id ?? null;
  const selectedId = decidedId ?? selectedProposalId;
  const incomplete =
    review.status === "failed_partial" ||
    review.status === "blocked_uncertain" ||
    review.status === "paused_budget";

  return (
    <div className="tech-detail">
      <p>
        <Link to="/tech">← Revues TECH</Link>
      </p>
      <div className="tech-detail__header">
        <h2>Revue TECH ({review.execution_mode})</h2>
        <span className="mission-status">{techStatusLabel(review.status)}</span>
      </div>
      <ReviewStatusBanner review={review} />
      <p className="demo-disclaimer">{review.disclaimer}</p>
      {incomplete ? (
        <div className="error-state" role="status">
          <p>
            Résultats incomplets — aucune décision/ADR complète tant que le pipeline
            n’est pas validé.
          </p>
        </div>
      ) : null}
      {review.scenario_label_note ? (
        <p className="demo-disclaimer" role="status">
          {review.scenario_label_note}
        </p>
      ) : null}
      <p className="muted">{review.request_text}</p>
      {review.snapshot ? (
        <p className="muted">
          Snapshot figé : {review.snapshot.project_name} — capturé{" "}
          {review.snapshot.captured_at}
        </p>
      ) : null}

      {review.execution_mode === "demo" ? <ScenarioSelectPanel review={review} /> : null}
      <RealLaunchPanel review={review} />
      <RealStepsPanel review={review} />
      <AnalysesPanel
        analyses={review.analyses}
        challenges={review.challenges}
        synthesis={review.synthesis}
        agentNames={names}
        showSlots={
          review.analyses.length > 0 ||
          review.synthesis != null ||
          review.status === "awaiting_decision" ||
          review.status === "decided" ||
          incomplete
        }
      />
      <ProposalsPanel
        proposals={review.proposals}
        selectedId={selectedId}
        decidedId={decidedId}
        selectable={review.status === "awaiting_decision"}
        onSelect={setSelectedProposalId}
      />
      <DecisionPanel review={review} proposalId={selectedId} />
      <AdrPanel decision={review.decision} adr={review.adr} />
    </div>
  );
}
