import { useMemo, useState } from "react";

import { ApiError } from "../../shared/api/client";
import type { CodePreviewDto, CodeSnapshotDto } from "./codeContextTypes";
import { SourceAttachBlock } from "./SourceAttachBlock";
import { SourcePreviewBlock } from "./SourcePreviewBlock";
import { SourceTreeBlock } from "./SourceTreeBlock";
import {
  useAttachSourceRootMutation,
  useCreatePreviewMutation,
  useDetachSourceRootMutation,
  useFreezeSnapshotMutation,
  useSourceRootQuery,
  useSourceTreeQuery,
} from "./useCodeContextQueries";

type Props = { projectId: string };

export function ProjectSourcesPanel({ projectId }: Props) {
  const root = useSourceRootQuery(projectId);
  const hasRoot = Boolean(root.data?.absolute_path);
  const tree = useSourceTreeQuery(projectId, hasRoot || root.data?.demo_fixture === true);
  const attach = useAttachSourceRootMutation(projectId);
  const detach = useDetachSourceRootMutation(projectId);
  const previewMut = useCreatePreviewMutation(projectId);
  const freezeMut = useFreezeSnapshotMutation(projectId);
  const [path, setPath] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [preview, setPreview] = useState<CodePreviewDto | null>(null);
  const [snapshot, setSnapshot] = useState<CodeSnapshotDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selectable = useMemo(
    () => (tree.data?.entries ?? []).filter((item) => item.kind === "file" && !item.excluded),
    [tree.data],
  );

  return (
    <section className="project-sources" aria-label="Sources code du projet">
      <h3>Sources code</h3>
      <p className="muted">
        Projet → sources → aperçu → snapshot → revue TECH. Lecture seule, aucun
        envoi OpenAI avant lancement explicite d’une revue.
      </p>
      {error ? (
        <div className="error-state" role="alert">
          <p>{error}</p>
        </div>
      ) : null}
      <SourceAttachBlock
        rootPath={root.data?.absolute_path}
        note={root.data?.note}
        path={path}
        onPath={setPath}
        busy={attach.isPending || detach.isPending}
        onAttach={() => {
          setError(null);
          attach.mutate(
            { absolute_path: path, exclusions: [] },
            {
              onSuccess: () => setPath(""),
              onError: (err) =>
                setError(err instanceof ApiError ? err.message : "Rattachement impossible"),
            },
          );
        }}
        onDetach={() => {
          setError(null);
          detach.mutate(undefined, {
            onError: (err) =>
              setError(err instanceof ApiError ? err.message : "Détachement impossible"),
          });
        }}
      />
      <SourceTreeBlock
        entries={selectable}
        all={tree.data?.entries ?? []}
        selected={selected}
        onToggle={(rel) =>
          setSelected((prev) =>
            prev.includes(rel) ? prev.filter((item) => item !== rel) : [...prev, rel],
          )
        }
        truncated={tree.data?.truncated ?? false}
        limitMessage={tree.data?.limit_message}
        disclaimer={tree.data?.secret_scan_disclaimer}
      />
      <SourcePreviewBlock
        selectedCount={selected.length}
        preview={preview}
        snapshot={snapshot}
        busy={previewMut.isPending || freezeMut.isPending}
        onPreview={() => {
          setError(null);
          previewMut.mutate(selected, {
            onSuccess: (data) => {
              setPreview(data);
              setSnapshot(null);
            },
            onError: (err) =>
              setError(err instanceof ApiError ? err.message : "Aperçu impossible"),
          });
        }}
        onFreeze={() => {
          if (!preview) return;
          setError(null);
          freezeMut.mutate(preview.preview_id, {
            onSuccess: setSnapshot,
            onError: (err) =>
              setError(err instanceof ApiError ? err.message : "Freeze impossible"),
          });
        }}
      />
    </section>
  );
}
