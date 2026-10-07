import { DemoModeBadge } from "../../features/runtime/DemoModeBadge";

type TopBarProps = {
  appName: string;
};

export function TopBar({ appName }: TopBarProps) {
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <h1 className="topbar__title">{appName}</h1>
        <DemoModeBadge />
      </div>
      <p className="topbar__tagline">Orchestrez vos projets. Des idées aux résultats.</p>
      <div className="topbar__meta">
        <span className="budget-badge" title="Le suivi budgétaire arrive au lot 3">
          Budget : Non activé
        </span>
      </div>
    </header>
  );
}
