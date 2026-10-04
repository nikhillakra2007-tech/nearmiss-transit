from backend.app.repositories.base import BaseRepository
from backend.app.db.models.agency import Agency
from backend.app.db.models.route import Route
from backend.app.db.models.stop import Stop
from backend.app.db.models.trip import Trip
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.service_alert import ServiceAlert
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import Pattern, NearMissPattern
from backend.app.db.models.investigation import Investigation, Evidence, CausalEdge
from backend.app.db.models.recommendation import Recommendation
from backend.app.db.models.intervention import Intervention
from backend.app.db.models.verification import Verification

class AgencyRepository(BaseRepository):
    model = Agency
class RouteRepository(BaseRepository):
    model = Route
class StopRepository(BaseRepository):
    model = Stop
class TripRepository(BaseRepository):
    model = Trip
class VehicleRepository(BaseRepository):
    model = Vehicle
class EventRepository(BaseRepository):
    model = TransitEvent
class ServiceAlertRepository(BaseRepository):
    model = ServiceAlert
class NearMissRepository(BaseRepository):
    model = NearMiss
class PatternRepository(BaseRepository):
    model = Pattern
class InvestigationRepository(BaseRepository):
    model = Investigation
class EvidenceRepository(BaseRepository):
    model = Evidence
class RecommendationRepository(BaseRepository):
    model = Recommendation
class InterventionRepository(BaseRepository):
    model = Intervention
class VerificationRepository(BaseRepository):
    model = Verification
