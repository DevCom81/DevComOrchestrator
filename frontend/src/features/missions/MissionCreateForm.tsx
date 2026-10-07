import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../shared/api/client";
import { Field } from "../../shared/ui/Field";
import { useProjectsQuery } from "../projects/useProjectsQueries";
import { REQUEST_MAX } from "./missionTypes";
import {
  useCreateMissionMutation,
  useDemoExamplesQuery,
} from "./useMissionsQueries";

export function MissionCreateForm() {
  const navigate = useNavigate();
  const projects = useProjectsQuery();
  const examples = useDemoExamplesQuery();
  const mutation = useCreateMissionMutation();
  const [projectId, setProjectId] = useState("");
  const [requestText, setRequestText] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const trimmed = requestText.trim();
    if (!projectId) {
      setError("Sélectionnez un projet.");
      return;
    }
    if (trimmed.length < 1 || trimmed.length > REQUEST_MAX) {
      setError(`La demande doit contenir entre 1 et ${REQUEST_MAX} caractères.`);
      return;
    }
    try {
      const mission = await mutation.mutateAsync({
        project_id: projectId,
        request_text: trimmed,
      });
      navigate(`/missions/${mission.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Création impossible.");
    }
  }

  return (
    <form className="mission-form" onSubmit={(event) => void onSubmit(event)} noValidate>
      <h2>Nouvelle mission</h2>
      {examples.data ? (
        <p className="demo-disclaimer">{examples.data.disclaimer}</p>
      ) : null}
      {examples.data ? (
        <div className="example-chips" aria-label="Exemples de demandes démo">
          {examples.data.items.map((example) => (
            <button
              key={example.id}
              type="button"
              className="example-chip"
              onClick={() => setRequestText(example.request_text)}
            >
              {example.label}
            </button>
          ))}
        </div>
      ) : null}
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <Field id="mission-project" label="Projet">
        <select
          id="mission-project"
          value={projectId}
          onChange={(event) => setProjectId(event.target.value)}
          required
        >
          <option value="">Choisir un projet…</option>
          {(projects.data?.items ?? []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </Field>
      <Field id="mission-request" label="Demande">
        <textarea
          id="mission-request"
          value={requestText}
          onChange={(event) => setRequestText(event.target.value)}
          rows={5}
          maxLength={REQUEST_MAX + 200}
          required
        />
      </Field>
      <button type="submit" className="button button--primary" disabled={mutation.isPending}>
        {mutation.isPending ? "Routage…" : "Créer et router"}
      </button>
    </form>
  );
}
