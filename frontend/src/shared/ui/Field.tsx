import type { ReactNode } from "react";

type FieldProps = {
  id: string;
  label: string;
  error?: string;
  children: ReactNode;
};

export function Field({ id, label, error, children }: FieldProps) {
  const errorId = `${id}-error`;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children}
      {error ? (
        <p id={errorId} className="field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
