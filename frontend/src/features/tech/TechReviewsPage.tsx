import { Link } from "react-router-dom";

import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { TechCreateForm } from "./TechCreateForm";
import { techStatusLabel } from "./techTypes";
import { useTechReviewsQuery } from "./useTechQueries";

export function TechReviewsPage() {
  const reviews = useTechReviewsQuery();

  return (
    <div className="tech-page">
      <div className="tech-page__header">
        <h2>Revue TECH</h2>
      </div>

      {reviews.isLoading ? <Spinner label="Chargement des revues…" /> : null}
      {reviews.isError ? (
        <ErrorState
          title="Impossible de charger les revues TECH"
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
                  <p className="project-list__desc">{techStatusLabel(review.status)}</p>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="Aucune revue TECH"
            message="Créez une revue fictive ci-dessous pour lancer un scénario déterministe."
          />
        )
      ) : null}

      <TechCreateForm />
    </div>
  );
}
