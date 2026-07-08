import csv
import io
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import functions_framework
from google.cloud import firestore, pubsub_v1, storage

TIMEZONE = "Asia/Kolkata"
DAILY_CSV_ITEM_QUOTA = 25
NAME_MAX_LENGTH = 100
MAX_PRICE = 9999.99
MAX_QUANTITY = 9999
REQUIRED_COLUMNS = ["name", "price", "is_veg"]

GCP_PROJECT_ID = os.environ["GCP_PROJECT_ID"]
PUBSUB_TOPIC_NAME = os.environ["PUBSUB_TOPIC_NAME"]

FS_CLIENT = firestore.Client()
gcs_client = storage.Client()
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(GCP_PROJECT_ID, PUBSUB_TOPIC_NAME)


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


def _validate_rows(rows: list[dict]) -> list[str]:
    """Returns a list of human-readable error strings, empty if every row is valid."""
    errors = []
    seen_names: dict[str, int] = {}

    for i, row in enumerate(rows, start=1):
        name = (row.get("name") or "").strip()
        if not name:
            errors.append(f"Row {i}: name is required")
        elif len(name) > NAME_MAX_LENGTH:
            errors.append(f"Row {i}: name exceeds {NAME_MAX_LENGTH} characters")
        elif name.lower() in seen_names:
            errors.append(
                f'Row {i}: duplicate name "{name}" (also used in row {seen_names[name.lower()]})'
            )
        else:
            seen_names[name.lower()] = i

        price_raw = row.get("price")
        try:
            price = float(price_raw)
            if not (0 < price <= MAX_PRICE):
                errors.append(f"Row {i}: price must be between 0 and {MAX_PRICE}")
        except (TypeError, ValueError):
            errors.append(
                f'Row {i}: price must be a positive number (got "{price_raw}")'
            )

        is_veg_raw = (row.get("is_veg") or "").strip().lower()
        if is_veg_raw not in ("true", "false"):
            errors.append(
                f'Row {i}: is_veg must be "true" or "false" (got "{row.get("is_veg")}")'
            )

        quantity_raw = row.get("quantity")
        if quantity_raw not in (None, ""):
            try:
                quantity = int(quantity_raw)
                if not (0 <= quantity <= MAX_QUANTITY):
                    errors.append(
                        f"Row {i}: quantity must be between 0 and {MAX_QUANTITY}"
                    )
            except ValueError:
                errors.append(
                    f'Row {i}: quantity must be a whole number (got "{quantity_raw}")'
                )

    return errors


@functions_framework.cloud_event
def csv_dispatch(cloud_event):
    """validates uploaded menu items CSV and dispatches rows for processing."""
    event_data = cloud_event.data
    bucket_name = event_data["bucket"]
    object_name = event_data["name"]
    restaurant_id, upload_id = object_name.split("/", 1)

    blob = gcs_client.bucket(bucket_name).blob(object_name)
    rows = list(csv.DictReader(io.StringIO(blob.download_as_text())))

    job_ref = FS_CLIENT.document(f"restaurants/{restaurant_id}/csvUploadJobs/{upload_id}")
    restaurant_ref = FS_CLIENT.document(f"restaurants/{restaurant_id}")
    owner_id = restaurant_ref.get().to_dict().get("ownerId")
    now = _now()

    missing_columns = [column for column in REQUIRED_COLUMNS if rows and column not in rows[0]]
    if not rows or missing_columns:
        job_ref.set(
            {
                "_id": upload_id,
                "restaurantId": restaurant_id,
                "ownerId": owner_id,
                "gcsPath": object_name,
                "status": "failed",
                "totalItems": len(rows),
                "successCount": 0,
                "failedCount": 0,
                "message": "CSV is empty or missing required columns: "
                + ", ".join(REQUIRED_COLUMNS),
                "_createdAt": now,
                "_updatedAt": now,
            }
        )
        return

    errors = _validate_rows(rows)
    if errors:
        job_ref.set(
            {
                "_id": upload_id,
                "restaurantId": restaurant_id,
                "ownerId": owner_id,
                "gcsPath": object_name,
                "status": "failed",
                "totalItems": len(rows),
                "successCount": 0,
                "failedCount": 0,
                "message": "\n".join(errors),
                "_createdAt": now,
                "_updatedAt": now,
            }
        )
        return

    transaction = FS_CLIENT.transaction()

    @firestore.transactional
    def _get_remaining_quota(transaction):
        snapshot = restaurant_ref.get(transaction=transaction)
        restaurant_data = snapshot.to_dict()
        metrics = restaurant_data.get("metrics", {})
        count = metrics.get("totalItemsUploadedToday", 0)
        today = _now().date().isoformat()
        if metrics.get("lastUploadDate") != today:
            count = 0
            transaction.update(
                restaurant_ref,
                {
                    "metrics.totalItemsUploadedToday": 0,
                    "metrics.lastUploadDate": today,
                },
            )
        return max(0, DAILY_CSV_ITEM_QUOTA - count)

    remaining = _get_remaining_quota(transaction)

    allowed_rows = rows[:remaining]
    quota_rejected_rows = rows[remaining:]

    job_ref.set(
        {
            "_id": upload_id,
            "restaurantId": restaurant_id,
            "ownerId": owner_id,
            "gcsPath": object_name,
            "status": "processing",
            "totalItems": len(rows),
            "successCount": 0,
            "failedCount": len(quota_rejected_rows),
            "message": "",
            "_createdAt": now,
            "_updatedAt": now,
        }
    )

    if quota_rejected_rows:
        batch = FS_CLIENT.batch()
        for i, row in enumerate(quota_rejected_rows, start=len(allowed_rows) + 1):
            item_ref = job_ref.collection("items").document(f"row-{i}")
            batch.set(
                item_ref,
                {
                    "_id": f"row-{i}",
                    "rowNumber": i,
                    "name": row["name"].strip(),
                    "status": "failed",
                    "message": "Daily upload quota exceeded",
                    "menuItemId": None,
                    "_createdAt": now,
                    "_updatedAt": now,
                },
            )
        batch.commit()

    for i, row in enumerate(allowed_rows, start=1):
        message_payload = {
            "restaurantId": restaurant_id,
            "jobId": upload_id,
            "itemRowId": f"row-{i}",
            "rowNumber": i,
            "name": row["name"].strip(),
            "description": row.get("description", "").strip(),
            "price": float(row["price"]),
            "isVeg": row["is_veg"].strip().lower() == "true",
            "quantity": int(row["quantity"]) if row.get("quantity") else None,
        }
        publisher.publish(topic_path, json.dumps(message_payload).encode("utf-8"))
