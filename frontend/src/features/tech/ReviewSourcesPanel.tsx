import type { CodeSourcesDto } from "./techTypes";

type Props = { sources: CodeSourcesDto | null | undefined };

export function ReviewSourcesPanel({ sources }: Props) {
  if (!sources) {
    return null;
  }
  return (
    <section className="tech-panel" aria-label="Sources de la revue">
      <h3>Sources utilisées</h3>
      <p role="status">{sources.notice}</p>
      {!sources.has_code_sources ? (
        <p className="tech-empty-state">
          Aucune source fichier : analyse fondée uniquement sur le contexte déclaré.
        </p>
      ) : (
        <>
          <p className="muted">
            Snapshot <code>{sources.snapshot_id}</code>
            {sources.fingerprint ? ` · ${sources.fingerprint.slice(0, 12)}…` : ""}
            {sources.git_commit
              ? ` · git ${sources.git_commit.slice(0, 8)}${
                  sources.git_dirty ? " (dirty)" : ""
                }`
              : ""}
          </p>
          {sources.git_note ? <p className="muted">{sources.git_note}</p> : null}
          <ul>
            {sources.files.map((file) => (
              <li key={file.relative_path}>
                <strong>{file.relative_path}</strong> — {file.byte_size} o —{" "}
                <code>{file.evidence_ref}</code>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
