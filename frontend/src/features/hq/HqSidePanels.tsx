import { Link } from "react-router-dom";

export function HqSidePanels() {
  return (
    <section className="hq-panels" aria-label="Panneaux d'information">
      <div className="hq-panel">
        <h2>Décisions à valider</h2>
        <p>Aucune décision en attente.</p>
      </div>
      <div className="hq-panel">
        <h2>Activité récente</h2>
        <p>Aucune activité pour le moment.</p>
      </div>
      <div className="hq-panel">
        <h2>Actions</h2>
        <p>Routage démo (missions) ou revue TECH fictive — moteurs IA non activés.</p>
        <Link to="/missions" className="button button--primary hq-panel__cta">
          + Nouvelle mission
        </Link>
        <Link to="/tech" className="button hq-panel__cta">
          + Revue TECH
        </Link>
      </div>
    </section>
  );
}
