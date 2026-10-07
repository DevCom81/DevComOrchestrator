import type { SpecialistAnalysisDto } from "./techTypes";

type Props = {
  agentId: string;
  displayName: string;
  analysis: SpecialistAnalysisDto | undefined;
};

export function SpecialistCard({ agentId, displayName, analysis }: Props) {
  return (
    <article className="tech-analysis-card" aria-label={displayName}>
      <h4>{displayName}</h4>
      {analysis ? (
        <>
          <p className="muted">{analysis.capability_id}</p>
          <FindingsBlock analysis={analysis} />
        </>
      ) : (
        <p className="tech-empty-state" role="status">
          Résultat absent — aucune analyse reçue pour « {agentId} ».
        </p>
      )}
    </article>
  );
}

function FindingsBlock({ analysis }: { analysis: SpecialistAnalysisDto }) {
  if (analysis.findings.length === 0) {
    return (
      <p className="tech-empty-state" role="status">
        Aucune observation dans ce domaine.
      </p>
    );
  }
  return (
    <ul>
      {analysis.findings.map((finding) => (
        <li key={finding.id}>
          <strong>{finding.risk_level}</strong> —{" "}
          {finding.observation.trim()
            ? finding.observation
            : "Observation absente (champ vide)."}
        </li>
      ))}
    </ul>
  );
}
