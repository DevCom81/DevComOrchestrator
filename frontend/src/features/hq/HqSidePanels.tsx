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
        <p>Les missions arriveront dans un prochain lot.</p>
        <button
          type="button"
          className="button button--primary hq-panel__cta"
          disabled
          aria-disabled="true"
          title="Bientôt"
        >
          + Nouvelle mission
        </button>
      </div>
    </section>
  );
}
