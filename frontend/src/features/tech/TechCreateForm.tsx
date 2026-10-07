import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../shared/api/client";
import { Field } from "../../shared/ui/Field";
import { useRuntimeQuery } from "../runtime/useRuntimeQuery";
import { useProjectsQuery } from "../projects/useProjectsQueries";
import { CodeSnapshotField } from "./CodeSnapshotField";
import { newIdempotencyKey, REQUEST_MAX, type ExecutionMode } from "./techTypes";
import { useCreateTechReviewMutation, useTechScenariosQuery } from "./useTechQueries";

export function TechCreateForm() {
  const navigate = useNavigate();
  const projects = useProjectsQuery();
  const scenarios = useTechScenariosQuery();
  const runtime = useRuntimeQuery();
  const mutation = useCreateTechReviewMutation();
  const [projectId, setProjectId] = useState("");
  const [requestText, setRequestText] = useState("");
  const [mode, setMode] = useState<ExecutionMode>("demo");
  const [codeSnapshotId, setCodeSnapshotId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const realEnabled = runtime.data?.real_mode_enabled ?? false;
  const keyOk = runtime.data?.openai_key_configured ?? false;

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
    if (mode === "real" && !realEnabled) {
      setError("Mode réel désactivé (DEVCOM_MODE=demo).");
      return;
    }
    try {
      const review = await mutation.mutateAsync({
        project_id: projectId,
        request_text: trimmed,
        idempotency_key: newIdempotencyKey("create"),
        execution_mode: mode,
        code_snapshot_id: codeSnapshotId.trim() || null,
      });
      navigate(`/tech/${review.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Création impossible.");
    }
  }

  return (
    <form className="tech-form" onSubmit={(event) => void onSubmit(event)} noValidate>
      <h2>Nouvelle revue TECH</h2>
      {scenarios.data ? <p className="demo-disclaimer">{scenarios.data.disclaimer}</p> : null}
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <fieldset className="tech-scenario-fieldset">
        <legend>Mode d’exécution</legend>
        <label className="tech-scenario-option">
          <input
            type="radio"
            name="exec-mode"
            checked={mode === "demo"}
            onChange={() => setMode("demo")}
          />
          <span>Démo (scénarios fictifs, aucun appel payant)</span>
        </label>
        <label className="tech-scenario-option">
          <input
            type="radio"
            name="exec-mode"
            checked={mode === "real"}
            onChange={() => setMode("real")}
            disabled={!realEnabled}
          />
          <span>
            Réel OpenAI {realEnabled ? "" : "(désactivé)"} — clé{" "}
            {keyOk ? "présente" : "absente"}
          </span>
        </label>
      </fieldset>
      <Field id="tech-project" label="Projet">
        <select
          id="tech-project"
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
      <Field id="tech-request" label="Demande">
        <textarea
          id="tech-request"
          value={requestText}
          onChange={(event) => setRequestText(event.target.value)}
          rows={4}
          maxLength={REQUEST_MAX + 200}
          required
        />
      </Field>
      <CodeSnapshotField value={codeSnapshotId} onChange={setCodeSnapshotId} />
      <button type="submit" className="button button--primary" disabled={mutation.isPending}>
        {mutation.isPending ? "Création…" : "Créer la revue"}
      </button>
    </form>
  );
}
