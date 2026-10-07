import { useEffect, useState, type FormEvent } from "react";

import { ApiError } from "../../shared/api/client";
import { ConfirmBanner } from "../../shared/ui/ConfirmBanner";
import { Field } from "../../shared/ui/Field";
import type { ProjectDto } from "./projectTypes";
import { validateProjectFields } from "./projectTypes";
import { useUpdateProjectMutation } from "./useProjectsQueries";

type ProjectEditFormProps = {
  project: ProjectDto;
};

export function ProjectEditForm({ project }: ProjectEditFormProps) {
  const mutation = useUpdateProjectMutation(project.id);
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description);
  const [fieldErrors, setFieldErrors] = useState<{
    name?: string;
    description?: string;
  }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setName(project.name);
    setDescription(project.description);
  }, [project.id, project.name, project.description]);

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
      await mutation.mutateAsync({
        name: name.trim(),
        description: description.trim(),
      });
      setSuccess("Modifications enregistrées.");
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.message);
        return;
      }
      setFormError("Enregistrement impossible.");
    }
  }

  return (
    <form className="project-form" onSubmit={(event) => void onSubmit(event)} noValidate>
      <h2>Modifier le projet</h2>
      {success ? <ConfirmBanner message={success} /> : null}
      {formError ? (
        <div className="error-state" role="alert">
          <p>{formError}</p>
        </div>
      ) : null}
      <Field id="edit-project-name" label="Nom" error={fieldErrors.name}>
        <input
          id="edit-project-name"
          name="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          aria-invalid={Boolean(fieldErrors.name)}
          maxLength={120}
          required
        />
      </Field>
      <Field
        id="edit-project-description"
        label="Description"
        error={fieldErrors.description}
      >
        <textarea
          id="edit-project-description"
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
          {mutation.isPending ? "Enregistrement…" : "Enregistrer"}
        </button>
      </div>
    </form>
  );
}
