import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";

export type AgentDto = {
  id: string;
  display_name: string;
  specialty_bullets: [string, string, string] | string[];
};

export type AgentListDto = {
  items: AgentDto[];
};

export function useAgentsQuery() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => apiGet<AgentListDto>("/api/agents"),
  });
}
