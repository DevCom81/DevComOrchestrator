import { DemoModeBadge } from "../../features/runtime/DemoModeBadge";
import { useRuntimeQuery } from "../../features/runtime/useRuntimeQuery";
import { formatEurMicros } from "../../features/tech/techTypes";

type TopBarProps = {
  appName: string;
};

export function TopBar({ appName }: TopBarProps) {
  const runtime = useRuntimeQuery();
  const budget = runtime.data?.budget;
  const confirmed = budget?.confirmed_eur_micros ?? 0;
  const reserved = budget?.reserved_eur_micros ?? 0;
  const cap = budget?.cap_eur_micros ?? 50_000_000;
  const title = budget
    ? `Confirmé ${formatEurMicros(confirmed)} · Réservé ${formatEurMicros(reserved)} · Plafond ${formatEurMicros(cap)}`
    : "Budget HQ";

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <h1 className="topbar__title">{appName}</h1>
        <DemoModeBadge />
      </div>
      <p className="topbar__tagline">Orchestrez vos projets. Des idées aux résultats.</p>
      <div className="topbar__meta">
        <span className="budget-badge" title={title}>
          Budget : {formatEurMicros(confirmed)} / {formatEurMicros(cap)}
        </span>
      </div>
    </header>
  );
}
