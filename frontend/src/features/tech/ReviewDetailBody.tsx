import type { TechReviewDto } from "./techTypes";
import { AnalysesPanel } from "./AnalysesPanel";
import { DecisionPanel } from "./DecisionPanel";
import { ProposalsPanel } from "./ProposalsPanel";
import { RealLaunchPanel } from "./RealLaunchPanel";
import { RealStepsPanel } from "./RealStepsPanel";
import { ReviewSourcesPanel } from "./ReviewSourcesPanel";
import { ScenarioSelectPanel } from "./ScenarioSelectPanel";
import { AdrPanel } from "./AdrPanel";

type Props = {
  review: TechReviewDto;
  agentNames: Map<string, string>;
  incomplete: boolean;
  selectedId: string | null;
  decidedId: string | null;
  onSelect: (id: string) => void;
};

export function ReviewDetailBody({
  review,
  agentNames,
  incomplete,
  selectedId,
  decidedId,
  onSelect,
}: Props) {
  return (
    <>
      <ReviewSourcesPanel sources={review.code_sources} />
      {review.execution_mode === "demo" ? <ScenarioSelectPanel review={review} /> : null}
      <RealLaunchPanel review={review} />
      <RealStepsPanel review={review} />
      <AnalysesPanel
        analyses={review.analyses}
        challenges={review.challenges}
        synthesis={review.synthesis}
        agentNames={agentNames}
        showSlots={
          review.analyses.length > 0 ||
          review.synthesis != null ||
          review.status === "awaiting_decision" ||
          review.status === "decided" ||
          incomplete
        }
      />
      <ProposalsPanel
        proposals={review.proposals}
        selectedId={selectedId}
        decidedId={decidedId}
        selectable={review.status === "awaiting_decision"}
        onSelect={onSelect}
      />
      <DecisionPanel review={review} proposalId={selectedId} />
      <AdrPanel decision={review.decision} adr={review.adr} />
    </>
  );
}
