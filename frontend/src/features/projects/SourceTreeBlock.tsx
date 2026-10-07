import type { TreeEntryDto } from "./codeContextTypes";

type Props = {
  entries: TreeEntryDto[];
  all: TreeEntryDto[];
  selected: string[];
  onToggle: (path: string) => void;
  truncated: boolean;
  limitMessage?: string | null;
  disclaimer?: string;
};

export function SourceTreeBlock(props: Props) {
  const refused = props.all.filter(
    (item) => item.excluded || item.kind === "symlink" || item.kind === "special",
  );
  return (
    <div className="project-sources__tree">
      <h4>Exploration (fichiers sélectionnables)</h4>
      {props.disclaimer ? <p className="muted">{props.disclaimer}</p> : null}
      {props.truncated ? (
        <p className="tech-empty-state" role="status">
          Limite d’exploration atteinte
          {props.limitMessage ? ` — ${props.limitMessage}` : ""}.
        </p>
      ) : null}
      <ul className="project-sources__list">
        {props.entries.map((item) => (
          <li key={item.relative_path}>
            <label>
              <input
                type="checkbox"
                checked={props.selected.includes(item.relative_path)}
                onChange={() => props.onToggle(item.relative_path)}
              />{" "}
              {item.relative_path}
            </label>
          </li>
        ))}
      </ul>
      {refused.length > 0 ? (
        <details>
          <summary>Entrées exclues / refusées</summary>
          <ul>
            {refused.map((item) => (
              <li key={`x-${item.relative_path}`}>
                {item.relative_path} — {item.exclusion_reason ?? item.kind}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}
