import type { CSSProperties } from "react";

import { presentationFor } from "./agentPresentation";
import type { AgentDto } from "./useAgentsQuery";

type AgentCardProps = {
  agent: AgentDto;
};

export function AgentCard({ agent }: AgentCardProps) {
  const presentation = presentationFor(agent.id);
  const accent = `var(--accent-${presentation.accentToken})`;
  const style = { "--agent-accent": accent } as CSSProperties;

  return (
    <article
      className="agent-card"
      style={style}
      aria-label={`${agent.display_name}, non activé`}
    >
      <div className="agent-card__header">
        <h3 className="agent-card__name">{agent.display_name}</h3>
        <span className="agent-card__status">
          <span className="agent-card__status-dot" aria-hidden="true" />
          Non activé
        </span>
      </div>
      <div className="agent-card__portrait">
        <img
          src={presentation.assetPath}
          alt=""
          width={320}
          height={320}
          decoding="async"
        />
      </div>
      <ul className="agent-card__skills">
        {agent.specialty_bullets.map((bullet) => (
          <li key={bullet}>{bullet}</li>
        ))}
      </ul>
    </article>
  );
}
