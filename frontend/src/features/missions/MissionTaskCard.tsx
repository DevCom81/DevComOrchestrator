import type { CSSProperties } from "react";

import { presentationFor } from "../hq/agentPresentation";
import type { TaskAssignmentDto } from "./missionTypes";

type MissionTaskCardProps = {
  task: TaskAssignmentDto;
  agentName: string;
};

export function MissionTaskCard({ task, agentName }: MissionTaskCardProps) {
  const presentation = presentationFor(task.agent_id);
  const style = {
    "--agent-accent": `var(--accent-${presentation.accentToken})`,
  } as CSSProperties;

  return (
    <article className="task-card" style={style}>
      <div className="task-card__portrait">
        <img
          src={presentation.assetPath}
          alt=""
          width={240}
          height={240}
          decoding="async"
        />
      </div>
      <h3>{agentName}</h3>
      <p>
        <strong>{task.capability_id}</strong>
      </p>
      <p>{task.rationale}</p>
    </article>
  );
}
