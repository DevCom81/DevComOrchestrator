import { useState } from "react";

import { ApiError } from "../../shared/api/client";
import type { TechReviewDto } from "./techTypes";
import { newIdempotencyKey } from "./techTypes";
import {
  useRunTechPipelineMutation,
  useSelectScenarioMutation,
  useTechScenariosQuery,
} from "./useTechQueries";

type Props = { review: TechReviewDto };

export function ScenarioSelectPanel({ review }: Props) {
  const scenarios = useTechScenariosQuery();
  const selectMutation = useSelectScenarioMutation(review.id);
  const runMutation = useRunTechPipelineMutation(review.id);
  const [scenarioId, setScenarioId] = useState(
    review.scenario_id ?? review.suggested_scenario_id ?? "",
  );
  const [error, setError] = useState<string | null>(null);

  async function confirmScenario() {
    setError(null);
    if (!scenarioId) {
      setError("Choisissez un scénario explicitement.");
      return;
    }
    try {
      await selectMutation.mutateAsync({ scenario_id: scenarioId });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sélection impossible.");
    }
  }

  async function runPipeline() {
    setError(null);
    try {
      await runMutation.mutateAsync({
        idempotency_key: newIdempotencyKey("run"),
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lancement impossible.");
    }
  }

  const canSelect =
    review.status === "selecting_scenario" || review.status === "ready_to_run";
  const canRun = review.status === "ready_to_run";

  return (
    <section className="tech-panel" aria-label="Scénario de démonstration">
      <h3>Scénario</h3>
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      {canSelect ? (
        <fieldset className="tech-scenario-fieldset">
          <legend>Sélection explicite</legend>
          {(scenarios.data?.items ?? []).map((item) => (
            <label key={item.id} className="tech-scenario-option">
              <input
                type="radio"
                name="scenario"
                value={item.id}
                checked={scenarioId === item.id}
                onChange={() => setScenarioId(item.id)}
              />
              <span>{item.label}</span>
            </label>
          ))}
        </fieldset>
      ) : (
        <p>
          Scénario figé : <strong>{review.scenario_id}</strong> v
          {review.scenario_version}
        </p>
      )}
      {canSelect && review.status === "selecting_scenario" ? (
        <button
          type="button"
          className="button button--primary"
          onClick={() => void confirmScenario()}
          disabled={selectMutation.isPending}
        >
          Confirmer le scénario
        </button>
      ) : null}
      {canRun ? (
        <button
          type="button"
          className="button button--primary"
          onClick={() => void runPipeline()}
          disabled={runMutation.isPending}
        >
          Lancer le pipeline démo
        </button>
      ) : null}
    </section>
  );
}
