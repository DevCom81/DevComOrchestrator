import { useState } from "react";

import { Field } from "../../shared/ui/Field";
import { newIdempotencyKey, type TechReviewDto } from "./techTypes";
import { useAcknowledgeUncertaintyMutation } from "./useTechQueries";

type Props = { review: TechReviewDto };

export function AcknowledgeUncertaintyPanel({ review }: Props) {
  const mutation = useAcknowledgeUncertaintyMutation(review.id);
  const [reason, setReason] = useState("");

  if (review.status !== "blocked_uncertain") {
    return null;
  }
  if (review.uncertainty_ack_at) {
    return (
      <section className="tech-block" aria-label="Incertitude prise en compte">
        <p>
          Incertitude prise en compte le {review.uncertainty_ack_at} — motif :{" "}
          {review.uncertainty_ack_reason}
        </p>
        <p className="muted">
          Ceci ne confirme pas le coût fournisseur et ne libère pas la réserve ambiguë.
        </p>
      </section>
    );
  }

  return (
    <section className="tech-block" aria-label="Acquitter l’incertitude">
      <p>
        Au moins un appel ou coût est incertain. Aucun retry LLM automatique. La
        réception/facturation fournisseur peut rester inconnue après une coupure.
      </p>
      <Field id="ack-reason" label="Motif (prise en compte humaine)">
        <textarea
          id="ack-reason"
          value={reason}
          maxLength={500}
          rows={3}
          onChange={(event) => setReason(event.target.value)}
        />
      </Field>
      <button
        type="button"
        disabled={!reason.trim() || mutation.isPending}
        onClick={() =>
          mutation.mutate({
            reason: reason.trim(),
            idempotency_key: newIdempotencyKey("ack"),
          })
        }
      >
        Pris en compte
      </button>
      {mutation.isError ? (
        <p className="muted" role="alert">
          {mutation.error.message}
        </p>
      ) : null}
    </section>
  );
}
