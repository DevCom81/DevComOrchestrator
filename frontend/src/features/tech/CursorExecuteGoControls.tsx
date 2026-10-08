import type { ApprovalDto, ExecutePreviewDto } from "./cursorTypes";
import { newIdempotencyKey } from "./techTypes";
import {
  useDecideGoMutation,
  useStartExecutionMutation,
} from "./useCursorQueries";

type Props = {
  preview: ExecutePreviewDto;
  planId: string;
  decide: ReturnType<typeof useDecideGoMutation>;
  start: ReturnType<typeof useStartExecutionMutation>;
  onStarted: () => void;
};

export function CursorExecuteGoControls({
  preview,
  planId,
  decide,
  start,
  onStarted,
}: Props) {
  return (
    <div>
      <h4>Payload exécution (à approuver)</h4>
      <pre>{preview.payload_json}</pre>
      <p>Budget : {JSON.stringify(preview.budget_layers)}</p>
      <button
        type="button"
        disabled={decide.isPending || start.isPending}
        onClick={() => {
          decide.mutate(
            { approvalId: preview.approval.id, grant: true },
            {
              onSuccess: (approval: ApprovalDto) => {
                start.mutate(
                  {
                    approval_id: approval.id,
                    idempotency_key: newIdempotencyKey("cursor-exec"),
                    payload_json: preview.payload_json,
                    payload_hash: preview.payload_hash,
                  },
                  { onSuccess: () => onStarted() },
                );
              },
            },
          );
        }}
      >
        Accorder GO et lancer (1 send)
      </button>
      <span className="sr-only">{planId}</span>
    </div>
  );
}
