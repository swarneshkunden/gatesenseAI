import io
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from schemas import CrowdStateUpdate
from rate_limiter import rate_limit_default, rate_limit_loose, rate_limit_strict
from gemini_service import GeminiService

logger = logging.getLogger("volunteer_copilot.routes.crowd")
router = APIRouter(prefix="/api/crowd", tags=["Crowd Operations"])

# In-memory storage for current crowd states
# Seeded with default values representing a partial bottleneck at Gate D and Corridor 2
current_zones = [
    {"zone_id": "Gate A", "occupancy_rate": 45.0, "throughput_rate": 120.0, "status": "Normal"},
    {"zone_id": "Gate B", "occupancy_rate": 65.0, "throughput_rate": 180.0, "status": "Normal"},
    {"zone_id": "Gate C", "occupancy_rate": 25.0, "throughput_rate": 70.0, "status": "Normal"},
    {"zone_id": "Gate D", "occupancy_rate": 82.0, "throughput_rate": 310.0, "status": "Crowded"},
    {"zone_id": "Corridor 1 (A-B)", "occupancy_rate": 50.0, "throughput_rate": 90.0, "status": "Normal"},
    {"zone_id": "Corridor 2 (C-D)", "occupancy_rate": 88.0, "throughput_rate": 220.0, "status": "Critical"},
]

def calculate_status(occupancy: float) -> str:
    if occupancy >= 85.0:
        return "Critical"
    elif occupancy >= 75.0:
        return "Crowded"
    return "Normal"

@router.get("/zones", dependencies=[Depends(rate_limit_default)])
async def get_zones():
    return {"status": "success", "zones": current_zones}

@router.post("/update", dependencies=[Depends(rate_limit_loose)])
async def update_zone(update: CrowdStateUpdate):
    """
    Manually update a specific zone's state with strict validation.
    """
    for zone in current_zones:
        if zone["zone_id"].lower() == update.zone_id.lower():
            zone["occupancy_rate"] = update.occupancy_rate
            zone["throughput_rate"] = update.throughput_rate
            zone["status"] = calculate_status(update.occupancy_rate)
            return {"status": "success", "message": f"Updated zone {zone['zone_id']}", "zone": zone}
            
    # If zone not found, add it
    new_zone = {
        "zone_id": update.zone_id,
        "occupancy_rate": update.occupancy_rate,
        "throughput_rate": update.throughput_rate,
        "status": calculate_status(update.occupancy_rate)
    }
    current_zones.append(new_zone)
    return {"status": "success", "message": f"Created zone {update.zone_id}", "zone": new_zone}

@router.post("/analyze", dependencies=[Depends(rate_limit_default)])
async def analyze_crowd(threshold: float = 80.0):
    """
    Triggers Gemini model reasoning over current zone capacities.
    """
    result = GeminiService.analyze_crowd(current_zones, threshold)
    return {"status": "success", "analysis": result}

@router.post("/upload-csv", dependencies=[Depends(rate_limit_strict)])
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV simulation configuration safely.
    Validates file extension, MIME type, size limits, and layout schema.
    No files are saved on disk in the web root; they are parsed strictly in memory.
    """
    # 1. Enforce strict size validation (max 100 KB for config files)
    MAX_SIZE = 100 * 1024 # 100 KB
    contents = await file.read(MAX_SIZE + 1)
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Max size allowed is 100 KB."
        )
        
    # 2. Enforce strict extension validation
    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    if ext != ".csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files (.csv) are allowed."
        )

    # 3. Enforce MIME type validation
    allowed_mimes = ["text/csv", "application/vnd.ms-excel", "application/octet-stream", "text/plain"]
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Content-Type header. Expected text/csv, got {file.content_type}."
        )

    # 4. Content Validation (attempt to parse CSV securely)
    try:
        csv_data = contents.decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_data))
        
        # Verify columns exist
        required_cols = {"zone_id", "occupancy_rate", "throughput_rate"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV must contain headers: {', '.join(required_cols)}"
            )

        # Validate rows and update our local zones state
        temp_zones = []
        for index, row in df.iterrows():
            try:
                # Instantiate CrowdStateUpdate to enforce schema validation per row
                validated = CrowdStateUpdate(
                    zone_id=str(row["zone_id"]),
                    occupancy_rate=float(row["occupancy_rate"]),
                    throughput_rate=float(row["throughput_rate"])
                )
                temp_zones.append({
                    "zone_id": validated.zone_id,
                    "occupancy_rate": validated.occupancy_rate,
                    "throughput_rate": validated.throughput_rate,
                    "status": calculate_status(validated.occupancy_rate)
                })
            except (ValueError, ValidationError) as ve:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Row {index + 1} validation failed: {str(ve)}"
                )

        # Update global memory zones
        global current_zones
        current_zones = temp_zones
        logger.info(f"Loaded {len(current_zones)} zones from uploaded CSV.")
        return {"status": "success", "message": f"Successfully loaded {len(current_zones)} zones from CSV.", "zones": current_zones}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to parse CSV upload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file content is invalid or corrupt and cannot be parsed as a CSV."
        )
