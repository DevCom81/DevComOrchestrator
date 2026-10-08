import { useState } from "react";

import { Field } from "../../shared/ui/Field";
import type { CursorExportDto, CursorReturnDto } from "./cursorTypes";

type Props = {
  canExport: boolean;
  onExport: () => void;
  exportItem: CursorExportDto | null;
  returns: CursorReturnDto[];
  onImport: (payload: {
    export_id: string;
    report_text: string;
    diff_text: string;
    declared_commit?: string;
  }) => void;
  busy: boolean;
};

export function CursorExportImport({
  canExport,
  onExport,
  exportItem,
  returns,
  onImport,
  busy,
}: Props) {
  const [report, setReport] = useState("");
  const [diff, setDiff] = useState("");
  const [commit, setCommit] = useState("");

  return (
    <section className="tech-panel" aria-label="Export et retour Cursor">
      <h4>Export / import</h4>
      <button type="button" disabled={busy || !canExport} onClick={onExport}>
        Créer export immuable
      </button>
      {exportItem ? (
        <div>
          <p className="muted">
            Export {exportItem.id.slice(0, 8)} · v{exportItem.plan_version} ·{" "}
            {exportItem.content_hash.slice(0, 12)}… (retéléchargeable sans nouveau GO)
          </p>
          <pre className="tech-adr-body">{exportItem.download_markdown}</pre>
        </div>
      ) : null}
      <Field id="cursor-report" label="Rapport Cursor (UTF-8, ≤ 200 KiB)">
        <textarea
          id="cursor-report"
          rows={4}
          value={report}
          onChange={(event) => setReport(event.target.value)}
        />
      </Field>
      <Field id="cursor-diff" label="Diff unifié (UTF-8, ≤ 1 MiB)">
        <textarea
          id="cursor-diff"
          rows={6}
          value={diff}
          onChange={(event) => setDiff(event.target.value)}
        />
      </Field>
      <Field id="cursor-commit" label="declared_commit (non probant)">
        <input
          id="cursor-commit"
          value={commit}
          onChange={(event) => setCommit(event.target.value)}
        />
      </Field>
      <button
        type="button"
        disabled={busy || !exportItem || !report.trim() || !diff.trim()}
        onClick={() =>
          exportItem &&
          onImport({
            export_id: exportItem.id,
            report_text: report,
            diff_text: diff,
            declared_commit: commit.trim() || undefined,
          })
        }
      >
        Importer retour
      </button>
      <ul className="tech-cost-list">
        {returns.map((item) => (
          <li key={item.id}>
            Retour {item.id.slice(0, 8)} → {item.verification_status}
            <span className="muted"> — {item.verification_notes}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
