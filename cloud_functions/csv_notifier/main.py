from datetime import datetime
from zoneinfo import ZoneInfo

import functions_framework
from google.cloud import firestore

TIMEZONE = "Asia/Kolkata"

FS_CLIENT = firestore.Client()


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


@functions_framework.cloud_event
def csv_notifier(cloud_event):
    """Email the restaurant owner when a CSV upload job finishes."""
    doc_path = cloud_event["subject"].removeprefix("documents/")
    job_ref = FS_CLIENT.document(doc_path)
    job_snapshot = job_ref.get()
    if not job_snapshot.exists:
        return
    job = job_snapshot.to_dict()

    if job.get("notifiedAt"):
        return

    status = job.get("status")
    total_items = job.get("totalItems", 0)
    success_count = job.get("successCount", 0)
    failed_count = job.get("failedCount", 0)
    is_complete = (
        status == "processing" and (success_count + failed_count) >= total_items
    )

    if status != "failed" and not is_complete:
        return

    owner_snapshot = FS_CLIENT.document(f"users/{job.get('ownerId')}").get()
    owner_email = (
        owner_snapshot.to_dict().get("email") if owner_snapshot.exists else None
    )
    if not owner_email:
        return

    now = _now()
    updates = {"notifiedAt": now}

    if status == "failed":
        subject = "Your menu CSV upload could not be processed"
        body = job.get("message", "")
    else:
        item_docs = job_ref.collection("items").order_by("rowNumber").get()
        lines = []
        for item_doc in item_docs:
            item = item_doc.to_dict()
            outcome = (
                "added"
                if item["status"] == "success"
                else f"failed ({item.get('message', '')})"
            )
            lines.append(f"Row {item['rowNumber']}: {item['name']} - {outcome}")
        subject = "Your menu CSV upload is complete"
        body = f"{success_count} of {total_items} items were added.\n\n" + "\n".join(
            lines
        )
        updates["status"] = "completed"

    FS_CLIENT.collection("mail").add(
        {
            "to": [owner_email],
            "message": {"subject": subject, "text": body},
            "_createdAt": now,
            "_updatedAt": now,
        }
    )
    job_ref.update(updates)
