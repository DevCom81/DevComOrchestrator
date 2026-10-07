import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { MissionCreateForm } from "../src/features/missions/MissionCreateForm";

vi.mock("../src/features/missions/useMissionsQueries", () => ({
  useDemoExamplesQuery: () => ({
    data: {
      disclaimer: "Routage de démonstration par règles déterministes.",
      items: [
        { id: "mail", label: "Classer des mails", request_text: "Classer ces mails" },
      ],
    },
  }),
  useCreateMissionMutation: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("../src/features/projects/useProjectsQueries", () => ({
  useProjectsQuery: () => ({
    data: { items: [{ id: "p1", name: "Demo", description: "x" }] },
  }),
}));

describe("MissionCreateForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("affiche le disclaimer et un exemple cliquable", () => {
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <MissionCreateForm />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    expect(
      screen.getByText(/Routage de démonstration par règles déterministes/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Classer des mails" })).toBeInTheDocument();
  });
});
