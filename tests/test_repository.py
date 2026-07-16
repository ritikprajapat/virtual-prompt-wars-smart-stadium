"""Tests for the VenueRepository abstraction and its two implementations."""
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.venue import Venue
from app.services.repository import JsonVenueRepository, VenueRepository
from app.services.venue_repository import load_venue


def test_json_repository_returns_the_bundled_venue():
    repo = JsonVenueRepository()
    venue = repo.load_venue()
    assert isinstance(venue, Venue)
    # Delegates to the process-cached loader, so it is the same object.
    assert venue is load_venue()


def test_in_memory_repository_returns_the_injected_venue(
    synthetic_venue, in_memory_venue_repository
):
    assert in_memory_venue_repository.load_venue() is synthetic_venue


def test_both_repositories_are_substitutable(in_memory_venue_repository):
    # Liskov: any VenueRepository can stand in for another; callers only ever
    # rely on the load_venue() contract returning a Venue.
    repos: list[VenueRepository] = [JsonVenueRepository(), in_memory_venue_repository]
    for repo in repos:
        assert isinstance(repo.load_venue(), Venue)


def test_create_app_uses_injected_repository(
    synthetic_venue, in_memory_venue_repository
):
    app = create_app(venue_repository=in_memory_venue_repository)
    assert app.state.venue_repository is in_memory_venue_repository
    assert app.state.venue is synthetic_venue


def test_injected_repository_drives_the_landing_page(in_memory_venue_repository):
    # The in-memory repository fully substitutes for the file-backed one:
    # the page renders from its data with no venue.json access.
    app = create_app(venue_repository=in_memory_venue_repository)
    with TestClient(app) as c:
        response = c.get("/")
    assert response.status_code == 200
    assert "Gate X" in response.text
