import type { ChallengeDto, SpecialistAnalysisDto, SynthesisDto } from "./techTypes";
import { TECH_SPECIALIST_IDS } from "./techTypes";
import { SpecialistCard } from "./SpecialistCard";

type Props = {
  analyses: SpecialistAnalysisDto[];
  challenges: ChallengeDto[];
  synthesis: SynthesisDto | null;
  agentNames: Map<string, string>;
  showSlots: boolean;
};

export function AnalysesPanel({
  analyses,
  challenges,
  synthesis,
  agentNames,
  showSlots,
}: Props) {
  if (!showSlots && analyses.length === 0 && !synthesis) {
    return null;
  }
  const byId = new Map(analyses.map((item) => [item.agent_id, item]));

  return (
    <section className="tech-panel" aria-label="Résultats des spécialistes">
      <h3>Six spécialistes</h3>
      <div className="tech-analysis-grid">
        {TECH_SPECIALIST_IDS.map((agentId) => (
          <SpecialistCard
            key={agentId}
            agentId={agentId}
            displayName={agentNames.get(agentId) ?? agentId}
            analysis={byId.get(agentId)}
          />
        ))}
      </div>

      {challenges.length > 0 ? (
        <>
          <h3>Contradiction</h3>
          <ul className="tech-challenge-list">
            {challenges.map((challenge) => (
              <li key={challenge.id}>
                <p>
                  <strong>
                    {agentNames.get(challenge.challenger_agent_id) ??
                      challenge.challenger_agent_id}
                  </strong>{" "}
                  sur {challenge.target_finding_id}
                </p>
                <p>{challenge.objection}</p>
                <p className="muted">Réponse : {challenge.author_response || "—"}</p>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <h3>Synthèse</h3>
      {synthesis ? (
        <>
          <p>{synthesis.summary}</p>
          {synthesis.disagreements.length > 0 ? (
            <ul>
              {synthesis.disagreements.map((item) => (
                <li key={item.id}>{item.summary}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">Aucun désaccord explicite dans la synthèse.</p>
          )}
        </>
      ) : (
        <p className="tech-empty-state" role="status">
          Synthèse absente — pipeline non terminé ou échec avant synthèse.
        </p>
      )}
    </section>
  );
}
