import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AgentCard } from "../src/features/hq/AgentCard";

describe("AgentCard", () => {
  it("affiche Non activé et conserve le portrait source", () => {
    render(
      <AgentCard
        agent={{
          id: "architecte",
          display_name: "Architecte",
          specialty_bullets: [
            "DDD, hexagonal et SOLID",
            "Frontières et dépendances",
            "Évolution et dette technique",
          ],
        }}
      />,
    );

    expect(screen.getByText("Non activé")).toBeInTheDocument();
    expect(screen.queryByText("Disponible")).not.toBeInTheDocument();
    const portrait = document.querySelector(".agent-card__portrait img");
    expect(portrait).not.toBeNull();
    expect(portrait?.getAttribute("src")).toBe("/agents/architecte.png");
  });
});
