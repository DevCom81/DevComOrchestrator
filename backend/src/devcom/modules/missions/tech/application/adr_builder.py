from __future__ import annotations

from devcom.modules.missions.tech.domain.artifacts import Proposal, Synthesis
from devcom.modules.missions.tech.domain.review import TechReview


def build_adr_body(review: TechReview, chosen: Proposal, rationale: str) -> str:
    alternatives = [item for item in review.proposals if item.id != chosen.id]
    disagreements = (
        _disagreements(review.synthesis) if review.synthesis is not None else ""
    )
    project_name = review.snapshot.project_name if review.snapshot else "n/a"
    sections = [
        f"# {chosen.title}",
        "## Contexte",
        review.request_text,
        f"Scénario `{review.scenario_id}` v{review.scenario_version}",
        f"Projet snapshot : {project_name}",
        "## Choix",
        chosen.solution,
        f"Effort : {chosen.effort.value}",
        "## Motif humain",
        rationale,
        "## Alternatives",
        _alternatives(alternatives),
        "## Compromis",
        "; ".join(chosen.tradeoffs) or "(aucun)",
        "## Risques",
        "; ".join(chosen.risks) or "(aucun)",
        "## Validations",
        "; ".join(chosen.validations) or "(aucune)",
        "## Désaccords conservés",
        disagreements or "(aucun)",
        "## Avertissement",
        "ADR de démonstration — n'autorise aucune implémentation.",
    ]
    return "\n\n".join(sections)


def _alternatives(proposals: list[Proposal]) -> str:
    if not proposals:
        return "(aucune)"
    return "\n".join(f"- {item.title} : {item.solution}" for item in proposals)


def _disagreements(synthesis: Synthesis) -> str:
    return "\n".join(f"- {item.summary}" for item in synthesis.disagreements)
