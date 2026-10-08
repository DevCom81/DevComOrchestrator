import { useState } from "react";

import { useSourceRootQuery } from "../projects/useCodeContextQueries";
import { CursorExecuteGoControls } from "./CursorExecuteGoControls";
import { CursorExecutionList } from "./CursorExecutionList";
import type {
  CursorExecutionDto,
  CursorPlanDto,
  ExecutePreviewDto,
} from "./cursorTypes";
import { newIdempotencyKey } from "./techTypes";
import {
  useApplyIntegrateMutation,
  useCancelExecutionMutation,
  useCursorExecutionsQuery,
  useDecideGoMutation,
  useRequestExecuteGoMutation,
  useRequestIntegrateGoMutation,
  useStartExecutionMutation,
} from "./useCursorQueries";

type Props = { plan: CursorPlanDto };

export function CursorExecutePanel({ plan }: Props) {
  const root = useSourceRootQuery(plan.project_id);
  const execs = useCursorExecutionsQuery(plan.id, true);
  const requestGo = useRequestExecuteGoMutation(plan.id);
  const decide = useDecideGoMutation();
  const start = useStartExecutionMutation(plan.id);
  const cancel = useCancelExecutionMutation(plan.id);
  const requestIntegrate = useRequestIntegrateGoMutation();
  const applyIntegrate = useApplyIntegrateMutation();
  const [preview, setPreview] = useState<ExecutePreviewDto | null>(null);
  const [observations, setObservations] = useState("");
  const [integrateHint, setIntegrateHint] = useState<string | null>(null);

  const sourceRoot = root.data?.absolute_path ?? "";
  const latest = execs.data?.items[0] ?? null;

  return (
    <section className="tech-panel" aria-label="Exécution Cursor">
      <h3>Exécution Cursor (liaison réelle)</h3>
      <p>
        GO execute ≠ GO export. Réservation DevCom ≠ plafond fournisseur.
        Manuel export/import reste en dépannage ci-dessous.
      </p>
      {!sourceRoot ? (
        <p role="status">Attachez un source root Git propre au projet.</p>
      ) : (
        <p>
          Root : <code>{sourceRoot}</code> — corrections utilisées :{" "}
          {plan.corrections_used}/2
        </p>
      )}
      <ExecuteActions
        sourceRoot={sourceRoot}
        plan={plan}
        latest={latest}
        observations={observations}
        requestPending={requestGo.isPending}
        onRequest={(body) =>
          requestGo.mutate(body, { onSuccess: (data) => setPreview(data) })
        }
      />
      {latest?.return_id ? (
        <label>
          Observations de revue (requis pour correction)
          <textarea
            value={observations}
            onChange={(event) => setObservations(event.target.value)}
            rows={3}
          />
        </label>
      ) : null}
      {preview ? (
        <CursorExecuteGoControls
          preview={preview}
          planId={plan.id}
          decide={decide}
          start={start}
          onStarted={() => setPreview(null)}
        />
      ) : null}
      <CursorExecutionList
        items={execs.data?.items ?? []}
        onCancel={(id) => cancel.mutate(id)}
        onIntegrate={(execution) =>
          runIntegrateFlow({
            execution,
            requestIntegrate,
            decide,
            applyIntegrate,
            onHint: setIntegrateHint,
          })
        }
      />
      {integrateHint ? <pre>{integrateHint}</pre> : null}
      {requestGo.isError ? <p role="alert">{requestGo.error.message}</p> : null}
      {start.isError ? <p role="alert">{start.error.message}</p> : null}
    </section>
  );
}

function ExecuteActions({
  sourceRoot,
  plan,
  latest,
  observations,
  requestPending,
  onRequest,
}: {
  sourceRoot: string;
  plan: CursorPlanDto;
  latest: CursorExecutionDto | null;
  observations: string;
  requestPending: boolean;
  onRequest: (body: {
    expected_version: number;
    idempotency_key: string;
    source_root: string;
    correction: boolean;
    prior_execution_id?: string;
    review_observations: string;
  }) => void;
}) {
  return (
    <div className="tech-actions">
      <button
        type="button"
        disabled={!sourceRoot || requestPending}
        onClick={() =>
          onRequest({
            expected_version: plan.plan_version,
            idempotency_key: newIdempotencyKey("cursor-ex-go"),
            source_root: sourceRoot,
            correction: false,
            review_observations: "",
          })
        }
      >
        Prévisualiser GO exécution
      </button>
      {latest?.return_id && plan.corrections_used < 2 ? (
        <button
          type="button"
          disabled={!sourceRoot || requestPending}
          onClick={() =>
            onRequest({
              expected_version: plan.plan_version,
              idempotency_key: newIdempotencyKey("cursor-corr-go"),
              source_root: sourceRoot,
              correction: true,
              prior_execution_id: latest.id,
              review_observations: observations,
            })
          }
        >
          Prévisualiser GO correction
        </button>
      ) : null}
    </div>
  );
}

function runIntegrateFlow({
  execution,
  requestIntegrate,
  decide,
  applyIntegrate,
  onHint,
}: {
  execution: CursorExecutionDto;
  requestIntegrate: ReturnType<typeof useRequestIntegrateGoMutation>;
  decide: ReturnType<typeof useDecideGoMutation>;
  applyIntegrate: ReturnType<typeof useApplyIntegrateMutation>;
  onHint: (hint: string) => void;
}) {
  const key = newIdempotencyKey("cursor-igo");
  requestIntegrate.mutate(
    { executionId: execution.id, idempotency_key: key },
    {
      onSuccess: (data) => {
        decide.mutate(
          { approvalId: data.approval.id, grant: true },
          {
            onSuccess: () => {
              applyIntegrate.mutate(
                {
                  executionId: execution.id,
                  approval_id: data.approval.id,
                  idempotency_key: newIdempotencyKey("cursor-apply"),
                },
                {
                  onSuccess: (integ) =>
                    onHint(integ.merge_hint ?? integ.summary ?? integ.status),
                },
              );
            },
          },
        );
      },
    },
  );
}
