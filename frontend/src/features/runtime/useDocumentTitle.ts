import { useEffect } from "react";

import { useRuntimeQuery } from "./useRuntimeQuery";

export function useDocumentTitle() {
  const runtime = useRuntimeQuery();

  useEffect(() => {
    if (!runtime.data) {
      return;
    }
    const modeLabel = runtime.data.mode === "real" ? "Mode réel" : "Mode démo";
    document.title = `DevCom HQ — ${modeLabel}`;
  }, [runtime.data]);
}
