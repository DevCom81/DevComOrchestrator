import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "../../shared/api/client";
import type { TechReviewDto } from "./techTypes";
import type {
  ApprovalDto,
  CursorExecutionDto,
  CursorExportDto,
  CursorIntegrationDto,
  CursorPlanDto,
  CursorReturnDto,
  ExecutePreviewDto,
  ReturnContextDto,
} from "./cursorTypes";

export function useCursorPlansQuery(reviewId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["cursor-plans", reviewId],
    queryFn: () =>
      apiGet<{ items: CursorPlanDto[] }>(
        `/api/tech/reviews/${reviewId}/cursor-plans`,
      ),
    enabled: Boolean(reviewId) && enabled,
  });
}

export function useCreateCursorPlanMutation(reviewId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiSend<CursorPlanDto>(
        `/api/tech/reviews/${reviewId}/cursor-plans`,
        "POST",
        {},
      ),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-plans", reviewId] });
    },
  });
}

export function useUpdateCursorPlanMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, string | number>) =>
      apiSend<CursorPlanDto>(`/api/cursor/plans/${planId}`, "PATCH", body),
    onSuccess: (data) => {
      void client.invalidateQueries({ queryKey: ["cursor-plans", data.review_id] });
    },
  });
}

export function useRequestGoMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { expected_version: number; idempotency_key: string }) =>
      apiSend<ApprovalDto>(`/api/cursor/plans/${planId}/request-go`, "POST", body),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-plans"] });
    },
  });
}

export function useDecideGoMutation() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (args: { approvalId: string; grant: boolean }) =>
      apiSend<ApprovalDto>(`/api/approvals/${args.approvalId}/decide`, "POST", {
        grant: args.grant,
      }),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-plans"] });
    },
  });
}

export function useExportPlanMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { idempotency_key: string }) =>
      apiSend<CursorExportDto>(`/api/cursor/plans/${planId}/export`, "POST", body),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-plans"] });
    },
  });
}

export function useImportReturnMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      export_id: string;
      report_text: string;
      diff_text: string;
      declared_base?: string;
      declared_commit?: string;
    }) =>
      apiSend<CursorReturnDto>(`/api/cursor/plans/${planId}/returns`, "POST", body),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-returns", planId] });
    },
  });
}

export function useCursorReturnsQuery(planId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["cursor-returns", planId],
    queryFn: () =>
      apiGet<{ items: CursorReturnDto[] }>(`/api/cursor/plans/${planId}/returns`),
    enabled: Boolean(planId) && enabled,
  });
}

export function useReturnContextQuery(returnId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["cursor-return-context", returnId],
    queryFn: () =>
      apiGet<ReturnContextDto>(`/api/cursor/returns/${returnId}/context`),
    enabled: Boolean(returnId) && enabled,
  });
}

export function useCreateReturnReviewMutation(returnId: string) {
  return useMutation({
    mutationFn: (body: { idempotency_key: string; execution_mode: string }) =>
      apiSend<TechReviewDto>(
        `/api/cursor/returns/${returnId}/tech-review`,
        "POST",
        body,
      ),
  });
}

export function useCursorExecutionsQuery(planId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["cursor-executions", planId],
    queryFn: () =>
      apiGet<{ items: CursorExecutionDto[] }>(
        `/api/cursor/plans/${planId}/executions`,
      ),
    enabled: Boolean(planId) && enabled,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const busy = items.some((item) =>
        ["intent", "running", "cancel_requested"].includes(item.status),
      );
      return busy ? 2000 : false;
    },
  });
}

export function useRequestExecuteGoMutation(planId: string) {
  return useMutation({
    mutationFn: (body: Record<string, string | number | boolean | null>) =>
      apiSend<ExecutePreviewDto>(
        `/api/cursor/plans/${planId}/request-execute-go`,
        "POST",
        body,
      ),
  });
}

export function useStartExecutionMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      approval_id: string;
      idempotency_key: string;
      payload_json: string;
      payload_hash: string;
    }) =>
      apiSend<CursorExecutionDto>(
        `/api/cursor/plans/${planId}/executions`,
        "POST",
        body,
      ),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-executions", planId] });
      void client.invalidateQueries({ queryKey: ["cursor-returns", planId] });
    },
  });
}

export function useCancelExecutionMutation(planId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (executionId: string) =>
      apiSend<CursorExecutionDto>(
        `/api/cursor/executions/${executionId}/cancel`,
        "POST",
        {},
      ),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["cursor-executions", planId] });
    },
  });
}

export function useRequestIntegrateGoMutation() {
  return useMutation({
    mutationFn: (args: { executionId: string; idempotency_key: string }) =>
      apiSend<{ preview: Record<string, unknown>; approval: ApprovalDto }>(
        `/api/cursor/executions/${args.executionId}/request-integrate-go`,
        "POST",
        { idempotency_key: args.idempotency_key },
      ),
  });
}

export function useApplyIntegrateMutation() {
  return useMutation({
    mutationFn: (args: {
      executionId: string;
      approval_id: string;
      idempotency_key: string;
    }) =>
      apiSend<CursorIntegrationDto>(
        `/api/cursor/executions/${args.executionId}/integrate`,
        "POST",
        {
          approval_id: args.approval_id,
          idempotency_key: args.idempotency_key,
        },
      ),
  });
}
