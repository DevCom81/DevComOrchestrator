import { useState, type FormEvent } from "react";

import { ApiError } from "../../shared/api/client";
import { Field } from "../../shared/ui/Field";
import type { TechReviewDto } from "./techTypes";
import { newIdempotencyKey, RATIONALE_MAX } from "./techTypes";
import { useDecideTechReviewMutation } from "./useTechQueries";

type Props = {
  review: TechReviewDto;
  proposalId: string | null;
};

export function DecisionPanel({ review, proposalId }: Props) {
  const mutation = useDecideTechReviewMutation(review.id);
  const [rationale, setRationale] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (review.status !== "awaiting_decision") {
    return null;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!proposalId) {
      setError("Sélectionnez une proposition ouverte.");
      return;
    }
    const text = rationale.trim();
    if (text.length < 1 || text.length > RATIONALE_MAX) {
      setError(`Motif requis (1–${RATIONALE_MAX} caractères).`);
      return;
    }
    try {
      await mutation.mutateAsync({
        proposal_id: proposalId,
        proposal_version: review.proposals_version,
        rationale: text,
        idempotency_key: newIdempotencyKey("decide"),
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Décision refusée.");
    }
  }

  return (
    <form className="tech-panel" onSubmit={(event) => void onSubmit(event)} noValidate>
      <h3>Décision humaine</h3>
      <p className="muted">Auteur de démonstration : local-demo-user</p>
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <Field id="tech-rationale" label="Motif (obligatoire)">
        <textarea
          id="tech-rationale"
          value={rationale}
          onChange={(event) => setRationale(event.target.value)}
          rows={4}
          maxLength={RATIONALE_MAX + 200}
          required
        />
      </Field>
      <button
        type="submit"
        className="button button--primary"
        disabled={mutation.isPending || !proposalId}
      >
        {mutation.isPending ? "Enregistrement…" : "Enregistrer la décision"}
      </button>
    </form>
  );
}
