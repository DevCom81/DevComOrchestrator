import { Field } from "../../shared/ui/Field";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function CodeSnapshotField({ value, onChange }: Props) {
  return (
    <>
      <Field
        id="tech-code-snapshot"
        label="Snapshot code (optionnel — UUID figé depuis le Projet)"
      >
        <input
          id="tech-code-snapshot"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="laisser vide = aucune source fichier"
        />
      </Field>
      <p className="muted">
        Sans snapshot : « Aucune source fichier : analyse fondée uniquement sur le
        contexte déclaré ». Figer un snapshot dans le détail Projet avant.
      </p>
    </>
  );
}
