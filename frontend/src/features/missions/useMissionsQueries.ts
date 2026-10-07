import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "../../shared/api/client";
import type {
  DemoExampleListDto,
  MissionDto,
  MissionListDto,
} from "./missionTypes";

export function useMissionsQuery(projectId?: string) {
  const suffix = projectId ? `?project_id=${encodeURIComponent(projectId)}` : "";
  return useQuery({
    queryKey: ["missions", projectId ?? "all"],
    queryFn: () => apiGet<MissionListDto>(`/api/missions${suffix}`),
  });
}

export function useMissionQuery(missionId: string) {
  return useQuery({
    queryKey: ["missions", "detail", missionId],
    queryFn: () => apiGet<MissionDto>(`/api/missions/${missionId}`),
    enabled: Boolean(missionId),
  });
}

export function useDemoExamplesQuery() {
  return useQuery({
    queryKey: ["missions", "demo-examples"],
    queryFn: () => apiGet<DemoExampleListDto>("/api/missions/demo-examples"),
  });
}

export function useCreateMissionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { project_id: string; request_text: string }) =>
      apiSend<MissionDto>("/api/missions", "POST", body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });
}

export function useAnswerClarificationMutation(missionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      clarification_token: string;
      answers: Record<string, string>;
    }) =>
      apiSend<MissionDto>(`/api/missions/${missionId}/clarifications`, "POST", body),
    onSuccess: async (mission) => {
      queryClient.setQueryData(["missions", "detail", missionId], mission);
      await queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });
}
