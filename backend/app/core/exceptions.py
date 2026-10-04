"""Typed exceptions → mapped to HTTP responses (no stack leak in prod)."""
from __future__ import annotations


class NearMissError(Exception):
    code = "INTERNAL_ERROR"
    status_code = 500


class FeedUnavailableError(NearMissError):
    code = "FEED_UNAVAILABLE"
    status_code = 502


class FeedParseError(NearMissError):
    code = "FEED_PARSE_ERROR"
    status_code = 502


class InvalidTransitEventError(NearMissError):
    code = "INVALID_TRANSIT_EVENT"
    status_code = 422


class EntityNotFoundError(NearMissError):
    code = "ENTITY_NOT_FOUND"
    status_code = 404


class DuplicateEventError(NearMissError):
    code = "DUPLICATE_EVENT"
    status_code = 409


class InvestigationError(NearMissError):
    code = "INVESTIGATION_ERROR"
    status_code = 409


class AgentProviderError(NearMissError):
    code = "AGENT_PROVIDER_ERROR"
    status_code = 502


class AgentOutputRejectedError(NearMissError):
    code = "AGENT_OUTPUT_REJECTED"
    status_code = 422


class UnsupportedInterventionError(NearMissError):
    code = "UNSUPPORTED_INTERVENTION"
    status_code = 422
