import { formatEurMicros, techStatusLabel, type TechReviewDto } from "./techTypes";

type Props = { review: TechReviewDto };

export function ReviewStatusBanner({ review }: Props) {
  const confirmed = review.usage
    .filter((item) => item.cost_status === "confirmed")
    .reduce((sum, item) => sum + item.eur_micros, 0);
  const reservation = review.reservation_status ?? "aucune";
  const synthesisLabel = review.synthesis ? "présente" : "absente";

  return (
    <section className="tech-status-banner" aria-label="Statut et budget de la revue">
      <p>
        <strong>Statut :</strong> {techStatusLabel(review.status)}
      </p>
      <p>
        <strong>Synthèse :</strong> {synthesisLabel}
      </p>
      {review.execution_mode === "real" ? (
        <p>
          <strong>Budget revue :</strong> confirmé {formatEurMicros(confirmed)}
          {review.envelope_eur_micros != null
            ? ` · enveloppe max ${formatEurMicros(review.envelope_eur_micros)}`
            : ""}
          {" · "}
          réservation {reservationLabel(reservation)}
        </p>
      ) : null}
    </section>
  );
}

function reservationLabel(status: string): string {
  switch (status) {
    case "settled":
      return "settled (reliquat libéré)";
    case "held":
      return "held (encore réservée)";
    case "overrun":
      return "overrun";
    case "aucune":
      return "non démarrée";
    default:
      return status;
  }
}
