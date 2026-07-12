"""Pydantic models mirroring the structure of app/data/venue.json."""
from pydantic import BaseModel, Field


class Gate(BaseModel):
    """An entry gate into the venue."""

    id: str
    name: str
    direction: str
    accessible: bool
    status: str


class Section(BaseModel):
    """A seating section within the venue."""

    id: str
    name: str
    block: str
    level: int
    gate_access: list[str]
    row_range: str
    accessible_seating: bool
    capacity: int


class Facility(BaseModel):
    """A named venue facility such as a lift, medical point, or prayer room."""

    id: str
    type: str
    name: str
    level: int
    accessible: bool


class Edge(BaseModel):
    """A walkable connection between two venue nodes."""

    from_: str = Field(alias="from")
    to: str
    distance_m: float
    walk_time_min: float
    step_free: bool

    model_config = {"populate_by_name": True}


class VenueInfo(BaseModel):
    """Top-level metadata describing the venue."""

    name: str
    city: str
    capacity: int


class Venue(BaseModel):
    """The full venue graph: metadata plus nodes and their connecting edges."""

    venue: VenueInfo
    gates: list[Gate]
    sections: list[Section]
    facilities: list[Facility]
    edges: list[Edge]


class RouteStep(BaseModel):
    """A single waypoint along a computed route."""

    node_id: str
    node_name: str
    distance_m: float
    walk_time_min: float


class Route(BaseModel):
    """A computed path across the venue with cumulative distance and time."""

    steps: list[RouteStep]
    total_distance_m: float
    total_walk_time_min: float
    step_free: bool
