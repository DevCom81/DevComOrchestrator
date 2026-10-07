import type { ProposalDto } from "./techTypes";

type Props = {
  proposals: ProposalDto[];
  selectedId: string | null;
  decidedId: string | null;
  onSelect: (proposalId: string) => void;
  selectable: boolean;
};

export function ProposalsPanel({
  proposals,
  selectedId,
  decidedId,
  onSelect,
  selectable,
}: Props) {
  if (proposals.length === 0) {
    return null;
  }
  return (
    <section className="tech-panel" aria-label="Propositions">
      <h3>Propositions</h3>
      <div className="tech-proposal-grid">
        {proposals.map((proposal) => (
          <ProposalCard
            key={proposal.id}
            proposal={proposal}
            chosen={decidedId === proposal.id}
            active={selectedId === proposal.id}
            selectable={selectable}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}

type CardProps = {
  proposal: ProposalDto;
  chosen: boolean;
  active: boolean;
  selectable: boolean;
  onSelect: (proposalId: string) => void;
};

function ProposalCard({ proposal, chosen, active, selectable, onSelect }: CardProps) {
  const className = chosen
    ? "tech-proposal tech-proposal--chosen"
    : active
      ? "tech-proposal tech-proposal--active"
      : "tech-proposal";
  return (
    <article className={className}>
      <h4>{proposal.title}</h4>
      <p>{proposal.solution}</p>
      <p className="muted">Effort {proposal.effort}</p>
      {proposal.blocked ? <BlockedNotice proposal={proposal} /> : null}
      {selectable && !proposal.blocked ? (
        <button
          type="button"
          className="button"
          onClick={() => onSelect(proposal.id)}
          aria-pressed={active}
        >
          Sélectionner
        </button>
      ) : null}
      {chosen ? <p className="tech-chosen-label">Choix retenu</p> : null}
    </article>
  );
}

function BlockedNotice({ proposal }: { proposal: ProposalDto }) {
  return (
    <div className="tech-block" role="status">
      <p>
        <strong>Bloquée</strong> — {proposal.block_reason}
      </p>
      <p className="muted">Levée indisponible dans ce lot. Conditions :</p>
      <ul>
        {proposal.lift_conditions.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
