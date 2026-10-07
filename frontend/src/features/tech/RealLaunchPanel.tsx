import { useState } from "react";

import { ApiError } from "../../shared/api/client";
import { formatEurMicros, newIdempotencyKey, type TechReviewDto } from "./techTypes";
import { useRunTechPipelineMutation } from "./useTechQueries";

type Props = { review: TechReviewDto };

export function RealLaunchPanel({ review }: Props) {
  const runMutation = useRunTechPipelineMutation(review.id);
  const [error, setError] = useState<string | null>(null);
  const frozen = review.frozen_plan as {
    models?: Record<string, { model: string; effort: string }>;
    max_calls?: number;
  } | null;
  const canRun = review.status === "ready_to_run";

  async function launch() {
    setError(null);
    try {
      await runMutation.mutateAsync({ idempotency_key: newIdempotencyKey("run-real") });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lancement réel impossible.");
    }
  }

  if (review.execution_mode !== "real") {
    return null;
  }

  return (
    <section className="tech-panel" aria-label="Lancement réel">
      <h3>Revue réelle — paramètres figés</h3>
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      {review.snapshot ? (
        <p className="muted">
          Contexte : {review.snapshot.project_name} (capturé {review.snapshot.captured_at})
        </p>
      ) : null}
      <ul className="tech-cost-list">
        <li>Appels max : {frozen?.max_calls ?? "—"}</li>
        <li>
          Enveloppe réservée :{" "}
          {review.envelope_eur_micros != null
            ? formatEurMicros(review.envelope_eur_micros)
            : "—"}{" "}
          (plafond revue 1,00 €)
        </li>
        <li>Réservation : {review.reservation_status ?? "non démarrée"}</li>
      </ul>
      {frozen?.models ? (
        <ul className="tech-cost-list">
          {Object.entries(frozen.models).map(([agent, cfg]) => (
            <li key={agent}>
              {agent} → {cfg.model} (effort {cfg.effort})
            </li>
          ))}
        </ul>
      ) : null}
      {canRun ? (
        <button
          type="button"
          className="button button--primary"
          onClick={() => void launch()}
          disabled={runMutation.isPending}
        >
          {runMutation.isPending ? "Démarrage…" : "Lancer la revue réelle"}
        </button>
      ) : null}
    </section>
  );
}
