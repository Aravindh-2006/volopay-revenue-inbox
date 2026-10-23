"""
Export module — generates output files, ZIP archives, and JSON manifests.

All exports are generated from the application's current stored data,
not from static files.
"""

import json
import csv
import os
import io
import zipfile
from datetime import datetime, timezone

from db import get_all_records, get_routes_for_record, get_connection, init_db


def generate_manifest(conn) -> list[dict]:
    """Build a manifest of all source records with their routing and state.

    Each row includes:
    - source_type, source_id, record_ref
    - applied_revision
    - route(s) — comma-separated
    - output_path(s)
    - review_state (pending / reviewed / stale)
    - manual_override (true/false)
    - analysis_freshness (fresh / stale)
    """
    records = get_all_records(conn)
    manifest = []

    for rec in records:
        routing = get_routes_for_record(conn, rec["source_type"], rec["source_id"])
        
        # Determine effective routes
        if routing["override"]:
            effective_routes = [routing["override"]["route"]]
            manual_override = True
        else:
            effective_routes = [s["route"] for s in routing["suggestions"]]
            manual_override = False

        output_paths = []
        # Add paths for each route
        for route in effective_routes:
            safe_ref = (rec["record_ref"] or "unknown").replace("/", "_")
            output_paths.append(f"output/{route}/{safe_ref}.json")

        manifest.append({
            "source_type": rec["source_type"],
            "source_id": rec["source_id"],
            "record_ref": rec["record_ref"],
            "applied_revision": rec["revision"],
            "routes": ", ".join(effective_routes) if effective_routes else "unclassified",
            "output_paths": ", ".join(output_paths) if output_paths else "",
            "review_state": rec["review_state"],
            "manual_override": manual_override,
            "analysis_freshness": "fresh" if rec["analysis_fresh"] else "stale",
            "has_transcript": bool(rec["has_usable_transcript"]),
        })

    return manifest


def generate_record_output(rec: dict, routing: dict) -> dict:
    """Generate the output JSON for a single record."""
    payload = json.loads(rec.get("payload_json", "{}"))
    transcript = None
    if rec.get("transcript_json"):
        try:
            transcript = json.loads(rec["transcript_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    # Determine effective routes
    if routing["override"]:
        effective_routes = [{"route": routing["override"]["route"],
                             "reason": routing["override"].get("reason", ""),
                             "source": "manual_override"}]
    else:
        effective_routes = [{"route": s["route"],
                             "reason": s.get("reason", ""),
                             "source": "automated"} for s in routing["suggestions"]]

    return {
        "source_type": rec["source_type"],
        "source_id": rec["source_id"],
        "record_ref": rec["record_ref"],
        "revision": rec["revision"],
        "review_state": rec["review_state"],
        "analysis_fresh": bool(rec["analysis_fresh"]),
        "has_usable_transcript": bool(rec["has_usable_transcript"]),
        "routes": effective_routes,
        "payload": payload,
        "transcript": transcript,
    }


def create_export_zip(conn) -> bytes:
    """Create a ZIP archive containing all exports.

    Contents:
    - manifest.json — full manifest
    - manifest.csv — CSV version of the manifest
    - output/<route>/<record_ref>.json — one file per record per route
    - manager_brief.md — the manager brief
    - findings.json — the three findings
    """
    from findings import generate_findings, generate_manager_brief

    records = get_all_records(conn)
    manifest = generate_manifest(conn)

    # Generate findings and brief
    findings_list = generate_findings(records)
    brief = generate_manager_brief(records, findings_list)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Manifest JSON
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))

        # Manifest CSV
        csv_buf = io.StringIO()
        if manifest:
            writer = csv.DictWriter(csv_buf, fieldnames=manifest[0].keys())
            writer.writeheader()
            writer.writerows(manifest)
        zf.writestr("manifest.csv", csv_buf.getvalue())

        # Individual record outputs
        for rec in records:
            routing = get_routes_for_record(conn, rec["source_type"], rec["source_id"])
            output = generate_record_output(rec, routing)

            if routing["override"]:
                routes_to_use = [routing["override"]["route"]]
            else:
                routes_to_use = [s["route"] for s in routing["suggestions"]]

            if not routes_to_use:
                routes_to_use = ["unclassified"]

            for route in routes_to_use:
                safe_ref = (rec["record_ref"] or "unknown").replace("/", "_")
                path = f"output/{route}/{safe_ref}.json"
                zf.writestr(path, json.dumps(output, indent=2, default=str))

        # Findings
        zf.writestr("findings.json", json.dumps(findings_list, indent=2, default=str))

        # Manager brief
        zf.writestr("manager_brief.md", brief)

    buf.seek(0)
    return buf.read()
