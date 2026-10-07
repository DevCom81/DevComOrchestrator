import { Link } from "react-router-dom";

import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { techStatusLabel } from "../tech/techTypes";
import { useTechReviewsQuery } from "../tech/useTechQueries";

type Props = { projectId: string };

export function ProjectReviewsPanel({ projectId }: Props) {
  const reviews = useTechReviewsQuery(projectId);

  return (
    <section className="project-reviews" aria-label="Revues TECH du projet">
      <h3>Revues TECH</h3>
      {reviews.isLoading ? <Spinner label="Chargement des revues…" /> : null}
      {reviews.isError ? (
        <ErrorState
          title="Revues indisponibles"
          message={reviews.error.message}
          onRetry={() => void reviews.refetch()}
        />
      ) : null}
      {!reviews.isLoading && !reviews.isError ? (
        reviews.data?.items.length ? (
          <ul className="tech-list">
            {reviews.data.items.map((review) => (
              <li key={review.id}>
                <Link to={`/tech/${review.id}`}>
                  <div className="project-list__name">{review.request_text}</div>
                  <p className="project-list__desc">
                    {review.execution_mode} · {techStatusLabel(review.status)}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="Aucune revue"
            message="Les revues liées à ce projet apparaîtront ici."
          />
        )
      ) : null}
    </section>
  );
}
