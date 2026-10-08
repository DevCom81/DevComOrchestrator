import { useEffect, useState } from "react";

import type { TechReviewDto } from "./techTypes";
import { newIdempotencyKey } from "./techTypes";
import type { ApprovalDto, CursorExportDto, CursorPlanDto } from "./cursorTypes";
import { CursorExecutePanel } from "./CursorExecutePanel";
import { CursorExportImport } from "./CursorExportImport";
import { CursorGoPanel } from "./CursorGoPanel";
import { CursorPlanEditor } from "./CursorPlanEditor";
import { CursorReturnReview } from "./CursorReturnReview";
import {
  useCreateCursorPlanMutation,
  useCursorPlansQuery,
  useCursorReturnsQuery,
  useDecideGoMutation,
  useExportPlanMutation,
  useImportReturnMutation,
  useRequestGoMutation,
  useUpdateCursorPlanMutation,
} from "./useCursorQueries";

type Props = { review: TechReviewDto };

export function CursorPlanPanel({ review }: Props) {
  if (review.status !== "decided") {
    return null;
  }
  return <CursorPlanPanelReady review={review} />;
}

function CursorPlanPanelReady({ review }: Props) {
  const plans = useCursorPlansQuery(review.id, true);
  const create = useCreateCursorPlanMutation(review.id);
  const plan = plans.data?.items[0] ?? null;

  return (
    <section className="tech-panel" aria-label="Plan Cursor">
      <h3>Plan Cursor</h3>
      {!plan ? (
        <button
          type="button"
          disabled={create.isPending}
          onClick={() => create.mutate()}
        >
          Préparer le plan d’implémentation
        </button>
      ) : (
        <CursorPlanWorkflow plan={plan} />
      )}
      {create.isError ? <p role="alert">{create.error.message}</p> : null}
    </section>
  );
}

function CursorPlanWorkflow({ plan }: { plan: CursorPlanDto }) {
  const [draft, setDraft] = useState(sectionsFrom(plan));
  const [approval, setApproval] = useState<ApprovalDto | null>(null);
  const [exportItem, setExportItem] = useState<CursorExportDto | null>(null);
  const update = useUpdateCursorPlanMutation(plan.id);
  const requestGo = useRequestGoMutation(plan.id);
  const decideGo = useDecideGoMutation();
  const exportPlan = useExportPlanMutation(plan.id);
  const importReturn = useImportReturnMutation(plan.id);
  const returns = useCursorReturnsQuery(plan.id, true);

  useEffect(() => {
    setDraft(sectionsFrom(plan));
  }, [plan]);

  const busy =
    update.isPending ||
    requestGo.isPending ||
    decideGo.isPending ||
    exportPlan.isPending ||
    importReturn.isPending;

  return (
    <>
      <CursorPlanEditor
        plan={plan}
        draft={draft}
        onChange={(key, value) => setDraft((prev) => ({ ...prev, [key]: value }))}
        saving={update.isPending}
        onSave={() =>
          update.mutate({
            expected_version: plan.plan_version,
            ...draft,
          })
        }
      />
      <details>
        <summary>Aperçu exact (markdown + manifeste)</summary>
        <pre className="tech-adr-body">{plan.preview_text}</pre>
      </details>
      <CursorGoPanel
        plan={plan}
        approval={approval}
        busy={busy}
        onRequest={() =>
          requestGo.mutate(
            {
              expected_version: plan.plan_version,
              idempotency_key: newIdempotencyKey("cursor-go"),
            },
            { onSuccess: setApproval },
          )
        }
        onGrant={() =>
          approval &&
          decideGo.mutate(
            { approvalId: approval.id, grant: true },
            { onSuccess: setApproval },
          )
        }
        onRefuse={() =>
          approval &&
          decideGo.mutate(
            { approvalId: approval.id, grant: false },
            { onSuccess: setApproval },
          )
        }
      />
      <CursorExecutePanel plan={plan} />
      <CursorExportImport
        canExport={approval?.status === "granted" || plan.status === "go_granted"}
        exportItem={exportItem}
        returns={returns.data?.items ?? []}
        busy={busy}
        onExport={() =>
          exportPlan.mutate(
            { idempotency_key: newIdempotencyKey("cursor-export") },
            { onSuccess: setExportItem },
          )
        }
        onImport={(payload) => importReturn.mutate(payload)}
      />
      {(returns.data?.items ?? []).map((item) => (
        <CursorReturnReview key={item.id} item={item} />
      ))}
    </>
  );
}

function sectionsFrom(plan: CursorPlanDto): Record<string, string> {
  return {
    objectif: plan.objectif,
    perimetre: plan.perimetre,
    exclusions: plan.exclusions,
    contraintes_architecture: plan.contraintes_architecture,
    criteres_acceptation: plan.criteres_acceptation,
    validations_attendues: plan.validations_attendues,
  };
}
