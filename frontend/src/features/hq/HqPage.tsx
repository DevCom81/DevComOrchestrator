import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { AgentCard } from "./AgentCard";
import { HqSidePanels } from "./HqSidePanels";
import { useAgentsQuery } from "./useAgentsQuery";

export function HqPage() {
  const agents = useAgentsQuery();

  if (agents.isLoading) {
    return <Spinner label="Chargement des agents…" />;
  }

  if (agents.isError) {
    return (
      <ErrorState
        title="Impossible de charger le HQ"
        message={agents.error.message}
        onRetry={() => void agents.refetch()}
      />
    );
  }

  const items = agents.data?.items ?? [];

  return (
    <div className="hq">
      <p className="hq__intro">
        Quartier général en mode démo. Les agents sont présentés pour référence ;
        leur moteur n&apos;est pas encore activé.
      </p>
      <section aria-label="Équipe d'agents">
        <div className="agent-grid">
          {items.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      </section>
      <HqSidePanels />
    </div>
  );
}
