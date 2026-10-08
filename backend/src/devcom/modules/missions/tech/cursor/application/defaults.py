from __future__ import annotations

from devcom.modules.missions.tech.domain.review import TechReview


def default_sections(review: TechReview) -> dict[str, str]:
    chosen = None
    if review.decision is not None:
        for proposal in review.proposals:
            if proposal.id == review.decision.proposal_id:
                chosen = proposal
                break
    title = chosen.title if chosen else "Option retenue"
    solution = chosen.solution if chosen else review.request_text
    risks = "; ".join(chosen.risks) if chosen and chosen.risks else "(à préciser)"
    validations = (
        "; ".join(chosen.validations) if chosen and chosen.validations else "(à préciser)"
    )
    return {
        "objectif": f"Implémenter : {title}",
        "perimetre": solution[:4000],
        "exclusions": (
            "Aucun push Git, aucun patch appliqué automatiquement, "
            "aucune commande exécutée depuis un import Cursor."
        ),
        "contraintes_architecture": (
            "Respecter monolithe modulaire, DDD pragmatique, hexagonal, SOLID, "
            "limites AGENTS.md et ADR existants."
        ),
        "criteres_acceptation": (
            f"Décision `{review.decision.proposal_id if review.decision else '?'}` ; "
            f"risques : {risks}"
        ),
        "validations_attendues": validations,
    }
