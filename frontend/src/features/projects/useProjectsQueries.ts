import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "../../shared/api/client";
import type { ProjectDto, ProjectListDto } from "./projectTypes";

export function useProjectsQuery() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiGet<ProjectListDto>("/api/projects"),
  });
}

export function useProjectQuery(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => apiGet<ProjectDto>(`/api/projects/${projectId}`),
    enabled: Boolean(projectId),
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; description: string }) =>
      apiSend<ProjectDto>("/api/projects", "POST", body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProjectMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; description?: string }) =>
      apiSend<ProjectDto>(`/api/projects/${projectId}`, "PATCH", body),
    onSuccess: async (project) => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}
