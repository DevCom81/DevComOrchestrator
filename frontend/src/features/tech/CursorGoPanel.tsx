import type { ApprovalDto, CursorPlanDto } from "./cursorTypes";

type Props = {
  plan: CursorPlanDto;
  approval: ApprovalDto | null;
  onRequest: () => void;
  onGrant: () => void;
  onRefuse: () => void;
  busy: boolean;
};

export function CursorGoPanel({
  plan,
  approval,
  onRequest,
  onGrant,
  onRefuse,
  busy,
}: Props) {
  return (
    <section className="tech-panel" aria-label="GO Cursor">
      <h4>GO d’export (distinct de la décision TECH)</h4>
      <p className="muted">Statut plan : {plan.status}</p>
      {approval ? (
        <p>
          GO {approval.status} · v{approval.resource_version} · expire{" "}
          {approval.expires_at}
          {approval.consumed_at ? ` · consommé ${approval.consumed_at}` : ""}
        </p>
      ) : (
        <p className="muted">Aucun GO actif.</p>
      )}
      <div className="tech-actions">
        <button type="button" disabled={busy} onClick={onRequest}>
          Demander GO
        </button>
        <button
          type="button"
          disabled={busy || approval?.status !== "pending"}
          onClick={onGrant}
        >
          Accorder
        </button>
        <button
          type="button"
          disabled={busy || approval?.status !== "pending"}
          onClick={onRefuse}
        >
          Refuser
        </button>
      </div>
    </section>
  );
}
