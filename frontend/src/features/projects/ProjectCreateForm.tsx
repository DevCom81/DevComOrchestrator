import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../shared/api/client";
import { ConfirmBanner } from "../../shared/ui/ConfirmBanner";
import { Field } from "../../shared/ui/Field";
import { validateProjectFields } from "./projectTypes";
import { useCreateProjectMutation } from "./useProjectsQueries";

export function ProjectCreateForm() {
  const navigate = useNavigate();
  const mutation = useCreateProjectMutation();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    description?: string;
  }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSuccess(null);
    const errors = validateProjectFields(name, description);
    setFieldErrors(errors);
    if (errors.name || errors.description) {
      return;
    }
    try {
      const project = await mutation.mutateAsync({
        name: name.trim(),
        description: description.trim(),
      });
      setSuccess("Projet créé.");
      navigate(`/projects/${project.id}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.message);
        return;
      }
      setFormError("Création impossible.");
    }
  }

  return (
    <form className="project-form" onSubmit={(event) => void onSubmit(event)} noValidate>
      <h2>Nouveau projet</h2>
      {success ? <ConfirmBanner message={success} /> : null}
      {formError ? (
        <div className="error-state" role="alert">
          <p>{formError}</p>
        </div>
      ) : null}
      <Field id="project-name" label="Nom" error={fieldErrors.name}>
        <input
          id="project-name"
          name="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          aria-invalid={Boolean(fieldErrors.name)}
          maxLength={120}
          required
        />
      </Field>
      <Field
        id="project-description"
        label="Description"
        error={fieldErrors.description}
      >
        <textarea
          id="project-description"
          name="description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          aria-invalid={Boolean(fieldErrors.description)}
          rows={5}
          maxLength={2500}
          required
        />
      </Field>
      <div className="project-form__actions">
        <button type="submit" className="button button--primary" disabled={mutation.isPending}>
          {mutation.isPending ? "Création…" : "Créer le projet"}
        </button>
      </div>
    </form>
  );
}
