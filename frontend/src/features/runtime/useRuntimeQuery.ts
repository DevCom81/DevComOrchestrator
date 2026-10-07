import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";

export type RuntimeDto = {
  mode: "demo";
  app_name: string;
  version: string;
};

export function useRuntimeQuery() {
  return useQuery({
    queryKey: ["runtime"],
    queryFn: () => apiGet<RuntimeDto>("/api/runtime"),
  });
}
