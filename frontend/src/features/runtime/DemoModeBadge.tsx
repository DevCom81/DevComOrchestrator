import { formatEurMicros } from "../tech/techTypes";
import { useRuntimeQuery } from "./useRuntimeQuery";

export function DemoModeBadge() {
  const runtime = useRuntimeQuery();
  const mode = runtime.data?.mode ?? "demo";
  const keyOk = runtime.data?.openai_key_configured ?? false;
  const budget = runtime.data?.budget;
  const title =
    mode === "real"
      ? `Mode réel — clé ${keyOk ? "présente" : "absente"}`
      : "Mode démo — aucune action payante";

  return (
    <span className="demo-badge" title={title}>
      {mode === "real" ? "Mode réel" : "Mode démo"}
      {mode === "real" ? ` · clé ${keyOk ? "OK" : "absente"}` : null}
      {budget ? ` · ${formatEurMicros(budget.confirmed_eur_micros)} / ${formatEurMicros(budget.cap_eur_micros)}` : null}
    </span>
  );
}
