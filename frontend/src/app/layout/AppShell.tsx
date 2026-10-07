import { Outlet } from "react-router-dom";

import { useRuntimeQuery } from "../../features/runtime/useRuntimeQuery";
import { ErrorState } from "../../shared/ui/ErrorState";
import { Spinner } from "../../shared/ui/Spinner";
import { SidebarNav } from "./SidebarNav";
import { TopBar } from "./TopBar";

export function AppShell() {
  const runtime = useRuntimeQuery();

  if (runtime.isLoading) {
    return (
      <div className="page">
        <Spinner label="Chargement du Command Center…" />
      </div>
    );
  }

  if (runtime.isError) {
    return (
      <div className="page">
        <ErrorState
          title="Command Center indisponible"
          message={runtime.error.message}
          onRetry={() => void runtime.refetch()}
        />
      </div>
    );
  }

  const appName = runtime.data?.app_name ?? "DevCom HQ";

  return (
    <div className="app-shell">
      <SidebarNav />
      <div className="shell-main">
        <TopBar appName={appName.includes("HQ") ? appName : "DevCom HQ"} />
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
