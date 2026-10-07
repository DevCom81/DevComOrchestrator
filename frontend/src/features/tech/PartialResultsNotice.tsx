import type { TechReviewDto } from "./techTypes";

type Props = { review: TechReviewDto };

const INCOMPLETE = new Set([
  "failed_partial",
  "interrupted",
  "blocked_uncertain",
  "paused_budget",
]);

export function PartialResultsNotice({ review }: Props) {
  if (!INCOMPLETE.has(review.status)) {
    return null;
  }
  const partial =
    review.analyses.length > 0 ||
    review.challenges.length > 0 ||
    review.synthesis != null ||
    review.usage.length > 0;
  return (
    <div className="error-state" role="status">
      <p>
        {partial
          ? "Résultats partiels disponibles — aucune décision/ADR complète tant que le pipeline n’est pas validé."
          : "Revue incomplète — aucune décision/ADR tant que le pipeline n’est pas validé."}
      </p>
    </div>
  );
}
