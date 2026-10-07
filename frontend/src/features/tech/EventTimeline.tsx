import type { TechEventDto } from "./techTypes";

type Props = { events: TechEventDto[]; loading: boolean };

export function EventTimeline({ events, loading }: Props) {
  if (loading && events.length === 0) {
    return <p className="muted">Chargement du journal…</p>;
  }
  if (events.length === 0) {
    return <p className="muted">Aucun événement journalisé pour cette revue.</p>;
  }
  return (
    <section className="tech-timeline" aria-label="Journal d’événements">
      <h3>Journal</h3>
      <ol className="tech-timeline__list">
        {events.map((event) => (
          <li key={event.id}>
            <span className="tech-timeline__seq">#{event.seq}</span>{" "}
            <strong>{event.event_type}</strong>
            <span className="muted"> · {formatStamp(event.occurred_at)}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function formatStamp(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(value));
}
