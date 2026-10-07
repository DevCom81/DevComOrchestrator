import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ProjectCreateForm } from "../src/features/projects/ProjectCreateForm";

function renderForm() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <ProjectCreateForm />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProjectCreateForm", () => {
  it("affiche une erreur de validation locale", async () => {
    const user = userEvent.setup();
    renderForm();
    await user.click(screen.getByRole("button", { name: "Créer le projet" }));
    expect(
      await screen.findByText(/Le nom doit contenir entre 1 et 80/),
    ).toBeInTheDocument();
  });
});
