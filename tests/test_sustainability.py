from app.models.sustainability import TransportMode
from app.services.sustainability import (
    compare_impact,
    draft_guidance,
    find_sustainability_touchpoint,
)
from tests.conftest import FakeLLMClient


async def test_draft_guidance_uses_injected_llm():
    # Proves the DIP seam: the impact comparison is computed deterministically,
    # then phrased by whatever LLMClient is injected.
    fake = FakeLLMClient("Nice choice — the bike racks are right by gate A.")
    comparison = compare_impact(TransportMode.WALK_BIKE)
    guidance = await draft_guidance("gate_a", comparison, "en", llm=fake)
    assert guidance == "Nice choice — the bike racks are right by gate A."
    assert fake.prompts[0]


def test_compare_impact_ranks_walk_bike_lowest():
    comparison = compare_impact(TransportMode.WALK_BIKE)
    assert comparison.impact_rank == 1
    assert comparison.lower_impact_modes == []


def test_compare_impact_ranks_rideshare_between_transit_and_car():
    comparison = compare_impact(TransportMode.RIDESHARE)
    assert comparison.impact_rank == 3
    assert comparison.lower_impact_modes == [
        TransportMode.WALK_BIKE,
        TransportMode.PUBLIC_TRANSIT,
    ]


def test_compare_impact_ranks_personal_car_highest():
    comparison = compare_impact(TransportMode.PERSONAL_CAR)
    assert comparison.impact_rank == 4
    assert comparison.lower_impact_modes == [
        TransportMode.WALK_BIKE,
        TransportMode.PUBLIC_TRANSIT,
        TransportMode.RIDESHARE,
    ]


def test_find_sustainability_touchpoint_returns_a_facility():
    touchpoint = find_sustainability_touchpoint()
    assert touchpoint is not None
    assert touchpoint.type in {
        "bike_parking",
        "recycling_point",
        "water_refill_station",
    }


def test_sustainability_endpoint_returns_comparison_and_guidance(client, mock_gemini):
    response = client.post(
        "/api/sustainability/advise",
        json={"start_node_id": "gate_a", "mode": "personal_car", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["guidance"] == "Mocked AI response."
    assert body["comparison"]["impact_rank"] == 4
    assert body["comparison"]["touchpoint"] is not None


def test_sustainability_endpoint_rejects_invalid_mode(client, mock_gemini):
    response = client.post(
        "/api/sustainability/advise",
        json={"start_node_id": "gate_a", "mode": "hyperloop", "language": "en"},
    )
    assert response.status_code == 422


def test_sustainability_endpoint_rejects_missing_start_node(client, mock_gemini):
    response = client.post(
        "/api/sustainability/advise",
        json={"mode": "walk_bike", "language": "en"},
    )
    assert response.status_code == 422
