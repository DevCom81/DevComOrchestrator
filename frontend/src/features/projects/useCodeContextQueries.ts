import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "../../shared/api/client";
import type {
  CodePreviewDto,
  CodeSnapshotDto,
  SourceRootDto,
  SourceTreeDto,
} from "./codeContextTypes";

export function useSourceRootQuery(projectId: string) {
  return useQuery({
    queryKey: ["projects", projectId, "source-root"],
    queryFn: () => apiGet<SourceRootDto | null>(`/api/projects/${projectId}/source-root`),
    enabled: Boolean(projectId),
  });
}

export function useSourceTreeQuery(projectId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["projects", projectId, "source-tree"],
    queryFn: () => apiGet<SourceTreeDto>(`/api/projects/${projectId}/source-tree`),
    enabled: Boolean(projectId) && enabled,
  });
}

export function useAttachSourceRootMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { absolute_path: string; exclusions: string[] }) =>
      apiSend<SourceRootDto>(`/api/projects/${projectId}/source-root`, "PUT", body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useDetachSourceRootMutation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiSend<void>(`/api/projects/${projectId}/source-root`, "DELETE"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useCreatePreviewMutation(projectId: string) {
  return useMutation({
    mutationFn: (relative_paths: string[]) =>
      apiSend<CodePreviewDto>(
        `/api/projects/${projectId}/code-context/preview`,
        "POST",
        { relative_paths },
      ),
  });
}

export function useFreezeSnapshotMutation(projectId: string) {
  return useMutation({
    mutationFn: (preview_id: string) =>
      apiSend<CodeSnapshotDto>(`/api/projects/${projectId}/code-snapshots`, "POST", {
        preview_id,
      }),
  });
}
