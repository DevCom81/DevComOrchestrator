import { Field } from "../../shared/ui/Field";

type Props = {
  rootPath?: string;
  note?: string | null;
  path: string;
  onPath: (value: string) => void;
  busy: boolean;
  onAttach: () => void;
  onDetach: () => void;
};

export function SourceAttachBlock(props: Props) {
  return (
    <div className="project-sources__attach">
      <p>
        Root actuel : <code>{props.rootPath ?? "aucun"}</code>
      </p>
      {props.note ? <p className="muted">{props.note}</p> : null}
      <Field id="source-path" label="Chemin absolu du dossier local">
        <input
          id="source-path"
          value={props.path}
          onChange={(event) => props.onPath(event.target.value)}
          placeholder="/chemin/absolu/vers/depot"
        />
      </Field>
      <div className="button-row">
        <button
          type="button"
          className="button button--primary"
          disabled={props.busy}
          onClick={props.onAttach}
        >
          Rattacher
        </button>
        <button
          type="button"
          className="button"
          disabled={props.busy || !props.rootPath}
          onClick={props.onDetach}
        >
          Détacher
        </button>
      </div>
    </div>
  );
}
