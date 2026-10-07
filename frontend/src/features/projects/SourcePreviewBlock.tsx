import type { CodePreviewDto, CodeSnapshotDto } from "./codeContextTypes";

type Props = {
  selectedCount: number;
  preview: CodePreviewDto | null;
  snapshot: CodeSnapshotDto | null;
  busy: boolean;
  onPreview: () => void;
  onFreeze: () => void;
};

export function SourcePreviewBlock(props: Props) {
  return (
    <div className="project-sources__preview">
      <h4>Aperçu déclaré → snapshot figé</h4>
      <p className="muted">
        Sélection déclarée : {props.selectedCount} fichier(s). L’aperçu fige des
        copies privées ; le freeze ne relit pas le disque source.
      </p>
      <div className="button-row">
        <button
          type="button"
          className="button button--primary"
          disabled={props.busy || props.selectedCount === 0}
          onClick={props.onPreview}
        >
          Prévisualiser
        </button>
        <button
          type="button"
          className="button"
          disabled={props.busy || !props.preview}
          onClick={props.onFreeze}
        >
          Figer le snapshot
        </button>
      </div>
      {props.preview ? <PreviewDetails preview={props.preview} /> : null}
      {props.snapshot ? (
        <p role="status">
          Snapshot figé <code>{props.snapshot.snapshot_id}</code>
          {props.snapshot.git_commit
            ? ` · git ${props.snapshot.git_commit.slice(0, 8)}${
                props.snapshot.git_dirty ? " (dirty)" : ""
              }`
            : ""}
          . Utilisable pour une revue TECH.
        </p>
      ) : null}
    </div>
  );
}

function PreviewDetails({ preview }: { preview: CodePreviewDto }) {
  return (
    <div>
      <p>
        preview_id <code>{preview.preview_id}</code> · empreinte{" "}
        <code>{preview.fingerprint.slice(0, 12)}…</code> · expire {preview.expires_at}
      </p>
      <p>
        Tokens (bloquant {preview.token_method_blocking}) : {preview.token_upper_bound} ·
        indicatif : {preview.token_indicative} · réserve budget : non · appels
        fournisseur : {preview.provider_calls}
      </p>
      {preview.files.map((file) => (
        <article key={file.relative_path} className="project-sources__file">
          <h5>
            {file.relative_path}{" "}
            <span className="muted">
              ({file.byte_size} o, {file.evidence_ref})
            </span>
          </h5>
          <pre>{file.content}</pre>
        </article>
      ))}
    </div>
  );
}
