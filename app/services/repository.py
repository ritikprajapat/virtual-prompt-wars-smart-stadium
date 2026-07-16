"""Substitutable sources of venue data behind a single interface.

``VenueRepository`` is the abstraction the composition root depends on for
loading the venue graph. Two interchangeable implementations back it: the
file-backed :class:`JsonVenueRepository` used in production and the
:class:`InMemoryVenueRepository` used in tests. Either can be dropped into
``create_app`` with identical results for every caller — the Liskov
substitution property — which is what lets tests run without touching disk.
"""
from abc import ABC, abstractmethod

from app.models.venue import Venue
from app.services.venue_repository import load_venue


class VenueRepository(ABC):
    """Interface for loading venue/gate/section/facility data."""

    @abstractmethod
    def load_venue(self) -> Venue:
        """Return the parsed venue graph."""


class JsonVenueRepository(VenueRepository):
    """Loads the venue from the bundled ``venue.json`` file.

    Delegates to the process-cached :func:`app.services.venue_repository.load_venue`
    so the JSON file is still read and parsed exactly once per process — the
    caching behaviour is unchanged from before this abstraction existed.
    """

    def load_venue(self) -> Venue:
        """Return the venue parsed from ``venue.json`` (cached per process)."""
        return load_venue()


class InMemoryVenueRepository(VenueRepository):
    """Serves a venue supplied directly at construction, with no file I/O.

    A legitimate second implementation — it lets tests and future callers
    provide any venue graph in memory rather than reading ``venue.json``.
    """

    def __init__(self, venue: Venue) -> None:
        """Store the venue this repository will serve on every load."""
        self._venue = venue

    def load_venue(self) -> Venue:
        """Return the venue this repository was constructed with."""
        return self._venue
