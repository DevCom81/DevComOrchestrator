export type AgentAccentToken =
  | "architecte"
  | "cyber"
  | "qa"
  | "devops"
  | "fullstack"
  | "sql_data"
  | "synthetiseur_tech"
  | "vendeur"
  | "secretaire"
  | "social"
  | "dispatcher";

export type AgentPresentation = {
  assetPath: string;
  accentToken: AgentAccentToken;
};

const PRESENTATION: Record<string, AgentPresentation> = {
  architecte: {
    assetPath: "/agents/architecte.png",
    accentToken: "architecte",
  },
  cyber: { assetPath: "/agents/cyber.png", accentToken: "cyber" },
  qa: { assetPath: "/agents/qa.png", accentToken: "qa" },
  devops: { assetPath: "/agents/devops.png", accentToken: "devops" },
  fullstack: { assetPath: "/agents/fullstack.png", accentToken: "fullstack" },
  sql_data: { assetPath: "/agents/sql_data.png", accentToken: "sql_data" },
  synthetiseur_tech: {
    assetPath: "/agents/synthetiseur_tech.png",
    accentToken: "synthetiseur_tech",
  },
  vendeur: { assetPath: "/agents/vendeur.png", accentToken: "vendeur" },
  secretaire: {
    assetPath: "/agents/secretaire.png",
    accentToken: "secretaire",
  },
  social: { assetPath: "/agents/social.png", accentToken: "social" },
  dispatcher: {
    assetPath: "/agents/dispatcher.png",
    accentToken: "dispatcher",
  },
};

export function presentationFor(agentId: string): AgentPresentation {
  const found = PRESENTATION[agentId];
  if (!found) {
    throw new Error(`missing presentation mapping for agent ${agentId}`);
  }
  return found;
}
