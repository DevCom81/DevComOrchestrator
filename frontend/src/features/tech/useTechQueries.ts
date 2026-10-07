import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "../../shared/api/client";
import type {
  ScenarioListDto,
  TechReviewDto,
  TechReviewListDto,
} from "./techTypes";

export function useTechReviewsQuery(projectId?: string) {
  const suffix = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return useQuery({
    queryKey: ["tech-reviews", projectId ?? "all"],
    queryFn: () => apiGet<TechReviewListDto>(`/api/tech/reviews${suffix}`),
  });
}

export function useTechReviewQuery(reviewId: string) {
  return useQuery({
    queryKey: ["tech-review", reviewId],
    queryFn: () => apiGet<TechReviewDto>(`/api/tech/reviews/${reviewId}`),
    enabled: Boolean(reviewId),
  });
}

export function useTechScenariosQuery() {
  return useQuery({
    queryKey: ["tech-scenarios"],
    queryFn: () => apiGet<ScenarioListDto>("/api/tech/scenarios"),
  });
}

export function useCreateTechReviewMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      project_id: string;
      request_text: string;
      idempotency_key: string;
    }) => apiSend<TechReviewDto>("/api/tech/reviews", "POST", body),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["tech-reviews"] });
    },
  });
}

export function useSelectScenarioMutation(reviewId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { scenario_id: string }) =>
      apiSend<TechReviewDto>(`/api/tech/reviews/${reviewId}/scenario`, "POST", body),
    onSuccess: (data) => {
      client.setQueryData(["tech-review", reviewId], data);
      void client.invalidateQueries({ queryKey: ["tech-reviews"] });
    },
  });
}

export function useRunTechPipelineMutation(reviewId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { idempotency_key: string }) =>
      apiSend<TechReviewDto>(`/api/tech/reviews/${reviewId}/run`, "POST", body),
    onSuccess: (data) => {
      client.setQueryData(["tech-review", reviewId], data);
      void client.invalidateQueries({ queryKey: ["tech-reviews"] });
    },
  });
}

export function useDecideTechReviewMutation(reviewId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      proposal_id: string;
      proposal_version: number;
      rationale: string;
      idempotency_key: string;
    }) =>
      apiSend<TechReviewDto>(`/api/tech/reviews/${reviewId}/decision`, "POST", body),
    onSuccess: (data) => {
      client.setQueryData(["tech-review", reviewId], data);
      void client.invalidateQueries({ queryKey: ["tech-reviews"] });
    },
  });
}
