import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";

export type BudgetSummaryDto = {
  month_id: string;
  cap_eur_micros: number;
  confirmed_eur_micros: number;
  reserved_eur_micros: number;
  uncertain_eur_micros: number;
};

export type RuntimeDto = {
  mode: "demo" | "real";
  app_name: string;
  version: string;
  openai_key_configured: boolean;
  real_mode_enabled: boolean;
  budget: BudgetSummaryDto;
};

export function useRuntimeQuery() {
  return useQuery({
    queryKey: ["runtime"],
    queryFn: () => apiGet<RuntimeDto>("/api/runtime"),
    refetchInterval: 15_000,
  });
}
