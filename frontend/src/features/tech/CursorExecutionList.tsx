import type { CursorExecutionDto } from "./cursorTypes";

type Props = {
  items: CursorExecutionDto[];
  onCancel: (id: string) => void;
  onIntegrate: (item: CursorExecutionDto) => void;
};

export function CursorExecutionList({ items, onCancel, onIntegrate }: Props) {
  if (!items.length) {
    return <p role="status">Aucune exécution.</p>;
  }
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>
          <strong>{item.status}</strong> — {item.id.slice(0, 8)} — base{" "}
          {item.git_base_commit.slice(0, 8)}
          {item.return_id ? ` — retour ${item.return_id.slice(0, 8)}` : ""}
          {item.error_message ? ` — ${item.error_message}` : ""}
          {["running", "cancel_requested"].includes(item.status) ? (
            <button type="button" onClick={() => onCancel(item.id)}>
              Demander arrêt
            </button>
          ) : null}
          {item.capture_manifest_sha && !item.capture_incomplete ? (
            <button type="button" onClick={() => onIntegrate(item)}>
              Intégrer (GO + branche locale)
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
