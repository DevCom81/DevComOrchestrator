import { Field } from "../../shared/ui/Field";
import type { CursorPlanDto } from "./cursorTypes";

type Props = {
  plan: CursorPlanDto;
  draft: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onSave: () => void;
  saving: boolean;
};

const FIELDS = [
  ["objectif", "Objectif"],
  ["perimetre", "Périmètre"],
  ["exclusions", "Exclusions"],
  ["contraintes_architecture", "Contraintes d'architecture"],
  ["criteres_acceptation", "Critères d'acceptation"],
  ["validations_attendues", "Validations attendues"],
] as const;

export function CursorPlanEditor({ plan, draft, onChange, onSave, saving }: Props) {
  return (
    <section aria-label="Édition du plan Cursor">
      <p className="muted">
        Version {plan.plan_version} · hash {plan.content_hash.slice(0, 12)}…
        {plan.code_snapshot_id
          ? ` · snapshot ${plan.code_snapshot_id.slice(0, 8)}`
          : " · Base source inconnue"}
      </p>
      {FIELDS.map(([key, label]) => (
        <Field key={key} id={`cursor-${key}`} label={label}>
          <textarea
            id={`cursor-${key}`}
            rows={3}
            value={draft[key] ?? ""}
            onChange={(event) => onChange(key, event.target.value)}
          />
        </Field>
      ))}
      <button type="button" disabled={saving} onClick={onSave}>
        Enregistrer (invalide le GO actif)
      </button>
    </section>
  );
}
