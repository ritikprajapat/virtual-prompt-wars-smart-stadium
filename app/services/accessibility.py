"""Matches accessibility needs to facilities and drafts a plain-language plan."""
from app.models.venue import Facility, Section
from app.services.gemini import ask_gemini
from app.services.i18n import language_name
from app.services.venue_repository import load_venue, node_name

_NEED_FACILITY_TYPES = {
    "wheelchair": {"elevator", "medical"},
    "hearing": {"medical"},
    "visual": {"medical"},
    "cognitive": {"prayer_room", "family_room", "medical"},
}


def find_accessible_section(target_node_id: str) -> Section | None:
    """Return the section if it has accessible seating, else None."""
    venue = load_venue()
    for section in venue.sections:
        if section.id == target_node_id:
            return section if section.accessible_seating else None
    return None


def relevant_facilities(need_type: str) -> list[Facility]:
    """List accessible facilities relevant to the given need type."""
    venue = load_venue()
    wanted_types = _NEED_FACILITY_TYPES.get(need_type, set())
    return [
        f
        for f in venue.facilities
        if f.accessible and (f.type in wanted_types or not wanted_types)
    ]


async def draft_accommodation_plan(
    need_type: str, target_node_id: str, language: str, notes: str | None
) -> str:
    """Ask Gemini for a short, step-by-step accommodation plan for the given need."""
    target_name = node_name(target_node_id)
    facilities = relevant_facilities(need_type)
    facility_names = ", ".join(f.name for f in facilities[:5]) or "none listed"
    lang_name = language_name(language)

    prompt = (
        f"You are an accessibility concierge at a stadium. A guest has a "
        f"{need_type} accessibility need and wants to reach {target_name}. "
        f"Nearby accessible facilities: {facility_names}. "
        f"Additional notes from the guest: {notes or 'none'}. "
        f"Write a short, clear, step-by-step accommodation plan in {lang_name}, "
        f"plain language, under 120 words, including which entrance and "
        f"facilities to use."
    )
    return await ask_gemini(prompt)
