"""Synthetic demo approval workflow. Actor switching is simulation, not authentication."""

import csv
import io
import json
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.database import connect
from backend.dependencies import get_settings
from backend.errors import AppError
from backend.repositories.predictions import get_prediction

router = APIRouter(tags=["Plan approval demo"])
ACTORS = {
    "demo-staff": {"id": "demo-staff", "name": "Demo staff", "role": "staff"},
    "demo-owner": {"id": "demo-owner", "name": "Demo owner", "role": "owner"},
}
SCHEMA = """
CREATE TABLE IF NOT EXISTS plan_reviews (
    review_id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL UNIQUE REFERENCES predictions(prediction_id),
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plan_review_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL REFERENCES plan_reviews(review_id),
    payload TEXT NOT NULL
);
"""


def initialize_reviews(database_path):
    with connect(database_path) as db:
        db.executescript(SCHEMA)


def actor(x_demo_actor: Annotated[str, Header()] = "demo-staff"):
    if x_demo_actor not in ACTORS:
        raise AppError("Unknown demo actor", 403)
    return ACTORS[x_demo_actor]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Submission(Input):
    prediction_id: str = Field(min_length=1, max_length=64)


class Revision(Input):
    expected_revision: int = Field(ge=1, strict=True)


class Quantity(Input):
    dish_id: str = Field(min_length=1, max_length=64)
    final_prep_quantity: int = Field(ge=0, le=1000000, strict=True)


class Edit(Revision):
    items: list[Quantity] = Field(min_length=1, max_length=1000)
    reason: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def unique_dishes(self):
        if len({item.dish_id for item in self.items}) != len(self.items):
            raise ValueError("Duplicate dishes are not allowed")
        return self


def now():
    return datetime.now(timezone.utc).isoformat()


def read(db, review_id):
    row = db.execute("SELECT payload FROM plan_reviews WHERE review_id=?", (review_id,)).fetchone()
    if row is None:
        raise AppError("Plan review not found", 404)
    return json.loads(row[0])


def record(db, plan, who, action, details):
    event = {
        "action": action,
        "actor": who,
        "timestamp": now(),
        "revision": plan["revision"],
        "details": details,
    }
    db.execute(
        "INSERT INTO plan_review_events(review_id,payload) VALUES (?,?)",
        (plan["review_id"], json.dumps(event, ensure_ascii=False)),
    )


def update(db, plan):
    db.execute(
        "UPDATE plan_reviews SET payload=? WHERE review_id=?",
        (json.dumps(plan, ensure_ascii=False), plan["review_id"]),
    )


def editable(plan, revision):
    if plan["status"] != "pending":
        raise AppError("Approved plans are locked. Generate a new forecast for a new plan.", 409)
    if plan["revision"] != revision:
        raise AppError("This plan changed. Refresh before continuing.", 409)


@router.get("/demo/actors")
def actors():
    return {
        "items": list(ACTORS.values()),
        "identity_mode": "simulated",
        "notice": "Synthetic demo only. Role switching is not secure authentication.",
    }


@router.post("/plan-reviews", status_code=201)
def submit(request: Submission, who=Depends(actor), settings=Depends(get_settings)):
    with connect(settings.database_path) as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute(
            "SELECT payload FROM plan_reviews WHERE prediction_id=?", (request.prediction_id,)
        ).fetchone()
        if existing:
            return json.loads(existing[0])
        prediction = get_prediction(db, request.prediction_id)
        plan = {
            "review_id": uuid4().hex,
            "prediction_id": request.prediction_id,
            "restaurant_id": "demo-restaurant",
            "identity_mode": "simulated",
            "status": "pending",
            "revision": 1,
            "created_at": now(),
            "submitted_by": who,
            "target_date": prediction["target_date"],
            "source": prediction["source"],
            "data_origin": prediction.get("data_origin"),
            "items": [
                {
                    "dish_id": x["dish_id"],
                    "dish_name": x["dish_name"],
                    "predicted_sales_quantity": x["predicted_sales_quantity"],
                    "recommended_prep_quantity": x["recommended_prep_quantity"],
                    "final_prep_quantity": x["recommended_prep_quantity"],
                }
                for x in prediction["items"]
            ],
        }
        db.execute(
            "INSERT INTO plan_reviews VALUES (?,?,?)",
            (plan["review_id"], request.prediction_id, json.dumps(plan, ensure_ascii=False)),
        )
        record(db, plan, who, "submitted", {"items": plan["items"]})
        return plan


@router.get("/plan-reviews")
def listing(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    who=Depends(actor),
    settings=Depends(get_settings),
):
    with connect(settings.database_path) as db:
        rows = db.execute(
            "SELECT payload FROM plan_reviews ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit, offset)
        )
        return {"items": [json.loads(x[0]) for x in rows], "limit": limit, "offset": offset}


@router.get("/plan-reviews/{review_id}")
def detail(review_id: str, who=Depends(actor), settings=Depends(get_settings)):
    with connect(settings.database_path) as db:
        plan = read(db, review_id)
        plan["events"] = [
            json.loads(x[0])
            for x in db.execute(
                "SELECT payload FROM plan_review_events WHERE review_id=? ORDER BY sequence",
                (review_id,),
            )
        ]
        return plan


@router.get("/plan-review-status/{prediction_id}")
def status(prediction_id: str, who=Depends(actor), settings=Depends(get_settings)):
    with connect(settings.database_path) as db:
        get_prediction(db, prediction_id)
        row = db.execute(
            "SELECT payload FROM plan_reviews WHERE prediction_id=?", (prediction_id,)
        ).fetchone()
        return {"review": json.loads(row[0]) if row else None}


@router.put("/plan-reviews/{review_id}")
def edit(review_id: str, request: Edit, who=Depends(actor), settings=Depends(get_settings)):
    with connect(settings.database_path) as db:
        db.execute("BEGIN IMMEDIATE")
        plan = read(db, review_id)
        editable(plan, request.expected_revision)
        quantities = {x.dish_id: x.final_prep_quantity for x in request.items}
        if set(quantities) != {x["dish_id"] for x in plan["items"]}:
            raise AppError("Include every dish exactly once", 422)
        changes = []
        for item in plan["items"]:
            changes.append(
                {
                    "dish_id": item["dish_id"],
                    "before": item["final_prep_quantity"],
                    "after": quantities[item["dish_id"]],
                }
            )
            item["final_prep_quantity"] = quantities[item["dish_id"]]
        plan["revision"] += 1
        update(db, plan)
        record(db, plan, who, "quantities_updated", {"reason": request.reason, "changes": changes})
        return plan


@router.post("/plan-reviews/{review_id}/approve")
def approve(review_id: str, request: Revision, who=Depends(actor), settings=Depends(get_settings)):
    if who["role"] != "owner":
        raise AppError("Only the demo owner can approve a final plan", 403)
    with connect(settings.database_path) as db:
        db.execute("BEGIN IMMEDIATE")
        plan = read(db, review_id)
        editable(plan, request.expected_revision)
        plan.update(
            status="approved", approved_by=who, approved_at=now(), revision=plan["revision"] + 1
        )
        update(db, plan)
        record(db, plan, who, "approved", {"items": plan["items"]})
        return plan


@router.get("/plan-reviews/{review_id}/export")
def export(review_id: str, who=Depends(actor), settings=Depends(get_settings)):
    with connect(settings.database_path) as db:
        plan = read(db, review_id)
        if plan["status"] != "approved":
            raise AppError("Approve this plan before exporting the final quantities", 409)
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(
            [
                "target_date",
                "dish_id",
                "dish_name",
                "final_prep_quantity",
                "approved_by",
                "approved_at",
                "identity_mode",
            ]
        )
        for item in plan["items"]:
            name = item["dish_name"]
            if name.lstrip().startswith(("=", "+", "-", "@")):
                name = "'" + name
            writer.writerow(
                [
                    plan["target_date"],
                    item["dish_id"],
                    name,
                    item["final_prep_quantity"],
                    plan["approved_by"]["name"],
                    plan["approved_at"],
                    "simulated",
                ]
            )
        return Response(
            "\ufeff" + stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="approved-prep-plan.csv"'},
        )
