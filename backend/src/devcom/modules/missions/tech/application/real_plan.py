from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from devcom.modules.billing.application.envelope import SPECIALISTS, ReviewEnvelope

CAPABILITIES = {
    "architecte": "tech.analyze.architecture",
    "cyber": "tech.analyze.security",
    "qa": "tech.analyze.quality",
    "devops": "tech.analyze.delivery",
    "fullstack": "tech.analyze.feasibility",
    "sql_data": "tech.analyze.data",
    "synthetiseur_tech": "tech.synthesize",
}


@dataclass(frozen=True, slots=True)
class PlannedStep:
    step_key: str
    phase: str
    agent_id: str
    capability_id: str
    model_id: str
    effort: str
    max_input: int
    max_output: int
    optional: bool
    depends_on: tuple[str, ...]


def build_real_plan(bounds: dict[str, Any], envelope: ReviewEnvelope) -> list[PlannedStep]:
    models = bounds["models"]
    token_bounds = bounds["token_bounds"]
    analyze = _specialist_phase("analyze", models, token_bounds, depends_on=(), optional=False)
    critique = _specialist_phase(
        "critique",
        models,
        token_bounds,
        depends_on=tuple(s.step_key for s in analyze),
        optional=False,
    )
    reply = _specialist_phase(
        "reply",
        models,
        token_bounds,
        depends_on=tuple(s.step_key for s in critique),
        optional=True,
    )
    steps = analyze + critique + reply
    synth = models["synthetiseur_tech"]
    steps.append(
        PlannedStep(
            step_key="synthesize",
            phase="synthesize",
            agent_id="synthetiseur_tech",
            capability_id=CAPABILITIES["synthetiseur_tech"],
            model_id=synth["model"],
            effort=synth["effort"],
            max_input=int(token_bounds["synthesize"]["max_input"]),
            max_output=int(token_bounds["synthesize"]["max_output"]),
            optional=False,
            depends_on=tuple(s.step_key for s in steps),
        )
    )
    assert len(steps) == envelope.max_calls
    return steps


def plan_as_dicts(steps: list[PlannedStep]) -> list[dict[str, Any]]:
    return [asdict(step) for step in steps]


def _specialist_phase(
    phase: str,
    models: dict[str, Any],
    token_bounds: dict[str, Any],
    *,
    depends_on: tuple[str, ...],
    optional: bool,
) -> list[PlannedStep]:
    steps: list[PlannedStep] = []
    for agent_id in SPECIALISTS:
        bound_key = f"{phase}_architecte" if agent_id == "architecte" else phase
        steps.append(
            PlannedStep(
                step_key=f"{phase}:{agent_id}",
                phase=phase,
                agent_id=agent_id,
                capability_id=CAPABILITIES[agent_id],
                model_id=models[agent_id]["model"],
                effort=models[agent_id]["effort"],
                max_input=int(token_bounds[bound_key]["max_input"]),
                max_output=int(token_bounds[bound_key]["max_output"]),
                optional=optional,
                depends_on=depends_on,
            )
        )
    return steps
