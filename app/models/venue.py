"""Pydantic models mirroring the structure of app/data/venue.json."""
from pydantic import BaseModel, Field


class Gate(BaseModel):
    id: str
    name: str
    direction: str
    accessible: bool
    status: str


class Section(BaseModel):
    id: str
    name: str
    block: str
    level: int
    gate_access: list[str]
    row_range: str
    accessible_seating: bool
    capacity: int


class Facility(BaseModel):
    id: str
    type: str
    name: str
    level: int
    accessible: bool


class Edge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    distance_m: float
    walk_time_min: float
    step_free: bool

    model_config = {"populate_by_name": True}


class VenueInfo(BaseModel):
    name: str
    city: str
    capacity: int


class Venue(BaseModel):
    venue: VenueInfo
    gates: list[Gate]
    sections: list[Section]
    facilities: list[Facility]
    edges: list[Edge]


class RouteStep(BaseModel):
    node_id: str
    node_name: str
    distance_m: float
    walk_time_min: float


class Route(BaseModel):
    steps: list[RouteStep]
    total_distance_m: float
    total_walk_time_min: float
    step_free: bool
