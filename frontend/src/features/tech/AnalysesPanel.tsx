import type { ChallengeDto, SpecialistAnalysisDto, SynthesisDto } from "./techTypes";

type Props = {
  analyses: SpecialistAnalysisDto[];
  challenges: ChallengeDto[];
  synthesis: SynthesisDto | null;
  agentNames: Map<string, string>;
};

export function AnalysesPanel({
  analyses,
  challenges,
  synthesis,
  agentNames,
}: Props) {
  if (analyses.length === 0) {
    return null;
  }
  return (
    <section className="tech-panel" aria-label="Résultats des spécialistes">
      <h3>Six spécialistes</h3>
      <div className="tech-analysis-grid">
        {analyses.map((analysis) => (
          <article key={analysis.agent_id} className="tech-analysis-card">
            <h4>{agentNames.get(analysis.agent_id) ?? analysis.agent_id}</h4>
            <p className="muted">{analysis.capability_id}</p>
            <ul>
              {analysis.findings.map((finding) => (
                <li key={finding.id}>
                  <strong>{finding.risk_level}</strong> — {finding.observation}
                </li>
              ))}
            </ul>
          </article>
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
                <p className="muted">Réponse : {challenge.author_response}</p>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {synthesis ? (
        <>
          <h3>Synthèse</h3>
          <p>{synthesis.summary}</p>
          {synthesis.disagreements.length > 0 ? (
            <ul>
              {synthesis.disagreements.map((item) => (
                <li key={item.id}>{item.summary}</li>
              ))}
            </ul>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
