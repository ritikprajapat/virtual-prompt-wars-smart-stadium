from app.services.accessibility import find_accessible_section, relevant_facilities


def test_relevant_facilities_filters_by_need_type():
    facilities = relevant_facilities("wheelchair")
    assert all(f.accessible for f in facilities)
    assert any(f.type == "elevator" for f in facilities)
    assert all(f.type in {"elevator", "medical"} for f in facilities)


def test_relevant_facilities_unknown_need_returns_all_accessible():
    facilities = relevant_facilities("unknown_need")
    assert all(f.accessible for f in facilities)
    assert len(facilities) > 0


def test_find_accessible_section_returns_none_for_inaccessible_section():
    assert find_accessible_section("sec_310") is None


def test_find_accessible_section_returns_section_when_accessible():
    section = find_accessible_section("sec_210")
    assert section is not None
    assert section.id == "sec_210"


def test_accessibility_endpoint_returns_plan_and_facilities(client, mock_gemini):
    response = client.post(
        "/api/accessibility/request",
        json={"need_type": "wheelchair", "target_node_id": "sec_210", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "Mocked AI response."
    assert isinstance(body["facilities"], list)


def test_accessibility_endpoint_rejects_invalid_need_type(client, mock_gemini):
    response = client.post(
        "/api/accessibility/request",
        json={"need_type": "not_a_need", "target_node_id": "sec_210", "language": "en"},
    )
    assert response.status_code == 422
