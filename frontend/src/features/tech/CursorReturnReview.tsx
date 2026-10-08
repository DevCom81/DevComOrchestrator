import { Link } from "react-router-dom";

import type { CursorReturnDto } from "./cursorTypes";
import { useCreateReturnReviewMutation, useReturnContextQuery } from "./useCursorQueries";
import { newIdempotencyKey } from "./techTypes";

type Props = { item: CursorReturnDto };

export function CursorReturnReview({ item }: Props) {
  const context = useReturnContextQuery(item.id, true);
  const createReview = useCreateReturnReviewMutation(item.id);

  return (
    <section className="tech-panel" aria-label="Revue du retour">
      <h4>Contexte immuable du retour</h4>
      {context.data ? (
        <>
          <p className="muted">{context.data.warning}</p>
          <p>
            Empreintes report={context.data.report_sha256.slice(0, 12)}… diff=
            {context.data.diff_sha256.slice(0, 12)}… · export v
            {context.data.export_plan_version}
          </p>
          <pre className="tech-adr-body">{context.data.diff_text}</pre>
        </>
      ) : (
        <p className="muted">Chargement du contexte…</p>
      )}
      {item.linked_review_id ? (
        <p>
          Revue liée : <Link to={`/tech/${item.linked_review_id}`}>{item.linked_review_id}</Link>
        </p>
      ) : (
        <button
          type="button"
          disabled={createReview.isPending}
          onClick={() =>
            createReview.mutate({
              idempotency_key: newIdempotencyKey("ret-review"),
              execution_mode: "demo",
            })
          }
        >
          Créer une revue TECH du retour (sans lancement)
        </button>
      )}
      {createReview.isError ? (
        <p role="alert">{createReview.error.message}</p>
      ) : null}
    </section>
  );
}
