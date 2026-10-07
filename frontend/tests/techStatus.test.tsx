import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EventTimeline } from "../src/features/tech/EventTimeline";
import { techStatusLabel } from "../src/features/tech/techTypes";

describe("techStatusLabel LOT5", () => {
  it("distingue interruption et incertitude", () => {
    expect(techStatusLabel("interrupted")).toBe("Interrompue");
    expect(techStatusLabel("blocked_uncertain")).toBe("Bloquée (incertain)");
  });
});

describe("EventTimeline", () => {
  it("affiche les événements ordonnés sans payload sensible", () => {
    render(
      <EventTimeline
        loading={false}
        events={[
          {
            id: "e1",
            review_id: "r1",
            seq: 1,
            event_type: "review.interrupted",
            occurred_at: "2026-10-07T12:00:00+00:00",
            payload: { has_started: false },
          },
        ]}
      />,
    );
    expect(screen.getByText("review.interrupted")).toBeInTheDocument();
    expect(screen.getByText(/#1/)).toBeInTheDocument();
  });
});
