import type { AdrDto, DecisionDto } from "./techTypes";

type Props = {
  decision: DecisionDto | null;
  adr: AdrDto | null;
};

export function AdrPanel({ decision, adr }: Props) {
  if (!decision || !adr) {
    return null;
  }
  return (
    <section className="tech-panel" aria-label="ADR de démonstration">
      <h3>{adr.title}</h3>
      <p className="demo-disclaimer">{adr.demo_warning}</p>
      <p>
        Choix <strong>{decision.proposal_id}</strong> par {decision.author} —{" "}
        {decision.decided_at}
      </p>
      <p>
        <em>Motif :</em> {decision.rationale}
      </p>
      <pre className="tech-adr-body">{adr.body}</pre>
    </section>
  );
}
