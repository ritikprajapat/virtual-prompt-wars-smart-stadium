"""Heuristic relative-impact comparison across arrival modes, phrased by Gemini.

The ranking below is a transparent, fixed ordering meant to nudge behavior — it is
not a real emissions calculation and makes no attempt to be one.
"""
from app.models.sustainability import ImpactComparison, TransportMode
from app.models.venue import Facility
from app.services.gemini import ask_gemini
from app.services.i18n import language_name
from app.services.venue_repository import load_venue, node_name

_IMPACT_ORDER = [
    TransportMode.WALK_BIKE,
    TransportMode.PUBLIC_TRANSIT,
    TransportMode.RIDESHARE,
    TransportMode.PERSONAL_CAR,
]

_MODE_LABELS = {
    TransportMode.WALK_BIKE: "walking or biking",
    TransportMode.PUBLIC_TRANSIT: "public transit",
    TransportMode.RIDESHARE: "rideshare or taxi",
    TransportMode.PERSONAL_CAR: "personal car",
}

_TOUCHPOINT_TYPES = {"bike_parking", "recycling_point", "water_refill_station"}


def find_sustainability_touchpoint() -> Facility | None:
    """First sustainability-relevant facility listed in the venue, if any."""
    venue = load_venue()
    return next((f for f in venue.facilities if f.type in _TOUCHPOINT_TYPES), None)


def compare_impact(mode: TransportMode) -> ImpactComparison:
    """Rank the chosen arrival mode against the others by fixed impact order."""
    rank = _IMPACT_ORDER.index(mode) + 1
    touchpoint = find_sustainability_touchpoint()
    return ImpactComparison(
        mode=mode,
        impact_rank=rank,
        lower_impact_modes=_IMPACT_ORDER[: rank - 1],
        touchpoint=touchpoint.name if touchpoint else None,
    )


async def draft_guidance(
    start_node_id: str, comparison: ImpactComparison, language: str
) -> str:
    """Ask Gemini for 2-3 friendly sentences nudging toward the lower-impact option."""
    start_name = node_name(start_node_id)
    mode_label = _MODE_LABELS[comparison.mode]
    lang_name = language_name(language)

    if comparison.lower_impact_modes:
        lower_labels = ", ".join(_MODE_LABELS[m] for m in comparison.lower_impact_modes)
        impact_note = f"Lower-impact options for this trip include: {lower_labels}."
    else:
        impact_note = "This is already the lowest-impact option available."

    touchpoint_note = (
        f"Mention this nearby sustainability touchpoint by name: "
        f"{comparison.touchpoint}."
        if comparison.touchpoint
        else "No specific sustainability touchpoint is listed yet — don't invent one."
    )

    prompt = (
        f"You are a friendly sustainability advisor at a stadium. "
        f"A fan starting from {start_name} "
        f"plans to arrive by {mode_label}. {impact_note} {touchpoint_note} "
        f"In {lang_name}, write 2-3 short, encouraging sentences: "
        f"acknowledge their plan, "
        f"nudge toward a lower-impact option only if one is reasonably "
        f"available, and if a "
        f"touchpoint was given, name it naturally. Keep it under 70 words and avoid "
        f"a lecturing tone."
    )
    return await ask_gemini(prompt)
