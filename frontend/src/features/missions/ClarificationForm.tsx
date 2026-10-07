import { useState, type FormEvent } from "react";

import { ApiError } from "../../shared/api/client";
import type { ClarificationQuestionDto } from "./missionTypes";
import { useAnswerClarificationMutation } from "./useMissionsQueries";

type ClarificationFormProps = {
  missionId: string;
  token: string;
  questions: ClarificationQuestionDto[];
};

export function ClarificationForm({
  missionId,
  token,
  questions,
}: ClarificationFormProps) {
  const mutation = useAnswerClarificationMutation(missionId);
  const question = questions[0];
  const [choiceId, setChoiceId] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!question) {
    return <p className="muted">Aucune question de clarification.</p>;
  }

  const questionId = question.id;
  const prompt = question.prompt;
  const choices = question.choices;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!choiceId) {
      setError("Choisissez une option.");
      return;
    }
    try {
      await mutation.mutateAsync({
        clarification_token: token,
        answers: { [questionId]: choiceId },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Réponse impossible.");
    }
  }

  return (
    <form className="mission-panel" onSubmit={(event) => void onSubmit(event)}>
      <h3>Clarification requise</h3>
      <p>{prompt}</p>
      <div className="clarification-choices" role="radiogroup" aria-label={prompt}>
        {choices.map((choice) => (
          <label key={choice.id}>
            <input
              type="radio"
              name={questionId}
              value={choice.id}
              checked={choiceId === choice.id}
              onChange={() => setChoiceId(choice.id)}
            />
            <span>{choice.label}</span>
          </label>
        ))}
      </div>
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <button type="submit" className="button button--primary" disabled={mutation.isPending}>
        {mutation.isPending ? "Envoi…" : "Valider le choix"}
      </button>
    </form>
  );
}
