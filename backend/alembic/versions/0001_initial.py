"""Initial schema — all 15 entities (revision 0001)."""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

JSONB_COL = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade():
    op.create_table("agencies", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("external_id", sa.String(128), unique=True, index=True),
                    sa.Column("name", sa.String(256)), sa.Column("timezone", sa.String(64), server_default="UTC"),
                    sa.Column("source_url", sa.String(512), nullable=True),
                    sa.Column("gtfs_static_url", sa.String(512), nullable=True),
                    sa.Column("gtfs_realtime_url", sa.String(512), nullable=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    for tbl, cols in [
        ("routes", [("agency_id", "agencies.id"), ("external_route_id", None), ("short_name", None), ("long_name", None), ("route_type", None)]),
        ("stops", [("agency_id", "agencies.id"), ("external_stop_id", None), ("name", None)]),
        ("vehicles", [("agency_id", "agencies.id"), ("external_vehicle_id", None), ("label", None)]),
    ]:
        op.create_table(tbl, sa.Column("id", sa.String(36), primary_key=True),
                        *[sa.Column(c, sa.String(128 if 'external' in c or c.endswith('_id') else 256),
                                    sa.ForeignKey(fk) if fk else None, index=True if c.endswith('_id') else False)
                          for c, fk in cols],
                        sa.Column("latitude", sa.Float(), nullable=True) if tbl == "stops" else sa.Column("x", sa.String(1), nullable=True),
                        sa.Column("longitude", sa.Float(), nullable=True) if tbl == "stops" else sa.Column("y", sa.String(1), nullable=True),
                        sa.Column("metadata", JSONB_COL, server_default="{}"),
                        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("trips", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("route_id", sa.String(36), sa.ForeignKey("routes.id"), index=True),
                    sa.Column("external_trip_id", sa.String(128), index=True),
                    sa.Column("service_date", sa.Date(), nullable=True),
                    sa.Column("direction_id", sa.Integer(), nullable=True),
                    sa.Column("start_time", sa.String(16), nullable=True),
                    sa.Column("metadata", JSONB_COL, server_default="{}"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("transit_events", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id"), index=True),
                    sa.Column("route_id", sa.String(36), sa.ForeignKey("routes.id"), nullable=True, index=True),
                    sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id"), nullable=True, index=True),
                    sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True, index=True),
                    sa.Column("stop_id", sa.String(36), sa.ForeignKey("stops.id"), nullable=True, index=True),
                    sa.Column("event_type", sa.String(32), index=True),
                    sa.Column("observed_at", sa.DateTime(timezone=True), index=True),
                    sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("delay_seconds", sa.Integer(), nullable=True),
                    sa.Column("latitude", sa.Float(), nullable=True), sa.Column("longitude", sa.Float(), nullable=True),
                    sa.Column("status", sa.String(32), server_default="OBSERVED"),
                    sa.Column("source", sa.String(32), server_default="gtfs-rt"),
                    sa.Column("source_event_id", sa.String(256), index=True),
                    sa.Column("raw_payload", JSONB_COL, server_default="{}"),
                    sa.Column("normalized_payload", JSONB_COL, server_default="{}"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.UniqueConstraint("agency_id", "source_event_id", name="uq_event_agency_source"))
    op.create_table("service_alerts", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id"), index=True),
                    sa.Column("route_id", sa.String(36), sa.ForeignKey("routes.id"), nullable=True),
                    sa.Column("external_alert_id", sa.String(128), index=True),
                    sa.Column("alert_type", sa.String(64), server_default="UNKNOWN"),
                    sa.Column("header", sa.String(512), nullable=True),
                    sa.Column("description", sa.String(2048), nullable=True),
                    sa.Column("severity", sa.String(32), server_default="INFO"),
                    sa.Column("active_from", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("active_until", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("raw_payload", JSONB_COL, server_default="{}"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("near_misses", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id"), index=True),
                    sa.Column("route_id", sa.String(36), sa.ForeignKey("routes.id"), nullable=True, index=True),
                    sa.Column("trip_id", sa.String(36), sa.ForeignKey("trips.id"), nullable=True),
                    sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
                    sa.Column("start_event_id", sa.String(36), sa.ForeignKey("transit_events.id")),
                    sa.Column("recovery_event_id", sa.String(36), sa.ForeignKey("transit_events.id"), nullable=True),
                    sa.Column("detected_at", sa.DateTime(timezone=True), index=True),
                    sa.Column("near_miss_type", sa.String(64)), sa.Column("severity", sa.String(16), server_default="MEDIUM"),
                    sa.Column("baseline_value", JSONB_COL, server_default="{}"),
                    sa.Column("abnormal_value", JSONB_COL, server_default="{}"),
                    sa.Column("recovery_duration_seconds", sa.Integer(), nullable=True),
                    sa.Column("confidence_score", sa.Float(), server_default="0.5"),
                    sa.Column("status", sa.String(32), server_default="DETECTED", index=True),
                    sa.Column("detection_reason", sa.String(2048), server_default=""),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("patterns", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("agency_id", sa.String(36), sa.ForeignKey("agencies.id"), index=True),
                    sa.Column("route_id", sa.String(36), sa.ForeignKey("routes.id"), nullable=True, index=True),
                    sa.Column("pattern_type", sa.String(64)), sa.Column("title", sa.String(512)),
                    sa.Column("description", sa.String(2048), server_default=""),
                    sa.Column("recurrence_count", sa.Integer(), server_default="1"),
                    sa.Column("first_seen_at", sa.DateTime(timezone=True)),
                    sa.Column("last_seen_at", sa.DateTime(timezone=True), index=True),
                    sa.Column("severity", sa.String(16), server_default="MEDIUM"),
                    sa.Column("confidence_score", sa.Float(), server_default="0.5"),
                    sa.Column("status", sa.String(32), server_default="OPEN", index=True),
                    sa.Column("features", JSONB_COL, server_default="{}"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("near_miss_patterns", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("near_miss_id", sa.String(36), sa.ForeignKey("near_misses.id"), index=True),
                    sa.Column("pattern_id", sa.String(36), sa.ForeignKey("patterns.id"), index=True),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.UniqueConstraint("near_miss_id", "pattern_id", name="uq_nm_pattern"))
    op.create_table("investigations", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("pattern_id", sa.String(36), sa.ForeignKey("patterns.id"), index=True),
                    sa.Column("status", sa.String(32), server_default="OPEN", index=True),
                    sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("investigation_summary", sa.String(4096), server_default=""),
                    sa.Column("confidence_score", sa.Float(), server_default="0.0"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("evidence", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("investigation_id", sa.String(36), sa.ForeignKey("investigations.id"), index=True),
                    sa.Column("evidence_type", sa.String(64)), sa.Column("source_entity_type", sa.String(64)),
                    sa.Column("source_entity_id", sa.String(36)),
                    sa.Column("description", sa.String(2048)),
                    sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("payload", JSONB_COL, server_default="{}"),
                    sa.Column("confidence_score", sa.Float(), server_default="0.8"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("causal_edges", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("investigation_id", sa.String(36), sa.ForeignKey("investigations.id"), index=True),
                    sa.Column("source_evidence_id", sa.String(36), sa.ForeignKey("evidence.id")),
                    sa.Column("target_evidence_id", sa.String(36), sa.ForeignKey("evidence.id")),
                    sa.Column("relationship_type", sa.String(64), server_default="MAY_CONTRIBUTE_TO"),
                    sa.Column("confidence_score", sa.Float(), server_default="0.5"),
                    sa.Column("explanation", sa.String(2048), server_default=""),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("recommendations", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("investigation_id", sa.String(36), sa.ForeignKey("investigations.id"), index=True),
                    sa.Column("recommendation_type", sa.String(64)), sa.Column("title", sa.String(512)),
                    sa.Column("description", sa.String(2048)), sa.Column("rationale", sa.String(2048), server_default=""),
                    sa.Column("expected_effect", sa.String(1024), server_default=""),
                    sa.Column("confidence_score", sa.Float(), server_default="0.5"),
                    sa.Column("status", sa.String(32), server_default="PROPOSED"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("interventions", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("recommendation_id", sa.String(36), sa.ForeignKey("recommendations.id"), index=True),
                    sa.Column("intervention_type", sa.String(64)), sa.Column("target", sa.String(512)),
                    sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("execution_status", sa.String(32), server_default="PROPOSED"),
                    sa.Column("execution_result", JSONB_COL, server_default="{}"),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_table("verifications", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("intervention_id", sa.String(36), sa.ForeignKey("interventions.id"), index=True),
                    sa.Column("verification_started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
                    sa.Column("verification_ended_at", sa.DateTime(timezone=True), nullable=True),
                    sa.Column("baseline_metrics", JSONB_COL, server_default="{}"),
                    sa.Column("post_metrics", JSONB_COL, server_default="{}"),
                    sa.Column("outcome", sa.String(32), server_default="INSUFFICIENT_DATA"),
                    sa.Column("confidence_score", sa.Float(), server_default="0.0"),
                    sa.Column("explanation", sa.String(2048), server_default=""),
                    sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade():
    for tbl in ["verifications", "interventions", "recommendations", "causal_edges", "evidence",
                "investigations", "near_miss_patterns", "patterns", "near_misses",
                "service_alerts", "transit_events", "trips", "vehicles", "stops", "routes", "agencies"]:
        op.drop_table(tbl)
