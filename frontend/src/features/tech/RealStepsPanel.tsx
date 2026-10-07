import { formatEurMicros, type TechReviewDto } from "./techTypes";

type Props = { review: TechReviewDto };

export function RealStepsPanel({ review }: Props) {
  if (review.execution_mode !== "real") {
    return null;
  }
  const confirmed = review.usage
    .filter((item) => item.cost_status === "confirmed")
    .reduce((sum, item) => sum + item.eur_micros, 0);
  const uncertain = review.usage
    .filter((item) => item.cost_status === "uncertain")
    .reduce((sum, item) => sum + item.eur_micros, 0);

  return (
    <section className="tech-panel" aria-label="Étapes et coûts réels">
      <h3>Étapes / coûts</h3>
      {review.failure_message ? (
        <div className="error-state" role="alert">
          <p>{review.failure_message}</p>
        </div>
      ) : null}
      <p className="muted">
        Confirmé {formatEurMicros(confirmed)} · Incertain {formatEurMicros(uncertain)}
        {review.envelope_eur_micros != null
          ? ` · Enveloppe max ${formatEurMicros(review.envelope_eur_micros)}`
          : null}
        {" · "}
        Réservation {review.reservation_status ?? "non démarrée"}
        {review.reservation_status === "settled" ? " (reliquat libéré)" : ""}
      </p>
      {review.steps.length === 0 ? (
        <p className="muted">Aucune étape démarrée — le GET ne déclenche aucun appel.</p>
      ) : (
        <ul className="tech-cost-list">
          {review.steps.map((step) => (
            <li key={step.step_key}>
              <strong>{step.step_key}</strong> — {step.status}
              {step.cost_status ? ` · coût ${step.cost_status}` : ""}
              {step.error_message ? ` · ${step.error_message}` : ""}
            </li>
          ))}
        </ul>
      )}
      {review.usage.length > 0 ? (
        <ul className="tech-cost-list">
          {review.usage.map((item) => (
            <li key={`${item.step_key}-${item.created_at}`}>
              {item.step_key}: {item.input_tokens}+{item.output_tokens} tok ·{" "}
              {formatEurMicros(item.eur_micros)} ({item.cost_status}/{item.result_status})
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
