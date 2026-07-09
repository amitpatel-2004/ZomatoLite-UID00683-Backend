from datetime import datetime
from zoneinfo import ZoneInfo

from google.cloud import firestore

from app.constants import TIMEZONE
from app.enums import FirestoreCollections
from app.internal.enums import CsvRowProcessingOutcome
from app.restaurants.menu_items.csv.enums import CsvUploadItemStatus
from app.restaurants.menu_items.dtos import CreateMenuItemPayloadDTO
from app.restaurants.menu_items.exceptions import DuplicateMenuItemNameError
from app.restaurants.menu_items.service import MenuItemService
from app.settings import FS_CLIENT


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


class CsvRowProcessingService:
    """Handles processing of a single CSV row delivered via Pub/Sub push."""

    def process_row(self, row: dict) -> CsvRowProcessingOutcome:
        """Create the menu item for a CSV row and record the outcome on the job.

        Args:
            row: The decoded Pub/Sub message payload for a single CSV row.

        Returns:
            Whether the row was already processed, succeeded, or failed.
        """
        restaurant_id = row["restaurantId"]
        job_id = row["jobId"]
        item_row_id = row["itemRowId"]

        item_ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
            f"/{FirestoreCollections.CSV_UPLOAD_JOBS.value}/{job_id}"
            f"/{FirestoreCollections.CSV_UPLOAD_JOB_ITEMS.value}/{item_row_id}"
        )
        existing = item_ref.get()
        if existing.exists and existing.to_dict().get("status") in (
            CsvUploadItemStatus.SUCCESS,
            CsvUploadItemStatus.FAILED,
        ):
            return CsvRowProcessingOutcome.PROCESSED

        job_ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
            f"/{FirestoreCollections.CSV_UPLOAD_JOBS.value}/{job_id}"
        )
        restaurant_ref = FS_CLIENT.document(
            f"{FirestoreCollections.RESTAURANTS.value}/{restaurant_id}"
        )
        now = _now()
        item_doc = {
            "_id": item_row_id,
            "rowNumber": row["rowNumber"],
            "name": row["name"],
            "menuItemId": None,
            "_createdAt": now,
            "_updatedAt": now,
        }

        payload = CreateMenuItemPayloadDTO.model_validate(row)
        batch = FS_CLIENT.batch()

        try:
            result = MenuItemService().add_menu_item(restaurant_id, payload)
        except DuplicateMenuItemNameError as err:
            item_doc.update({"status": CsvUploadItemStatus.FAILED, "message": err.detail})
            batch.set(item_ref, item_doc)
            batch.update(
                job_ref, {"failedCount": firestore.Increment(1), "_updatedAt": now}
            )
            batch.commit()
            return CsvRowProcessingOutcome.FAILED

        item_doc.update(
            {
                "status": CsvUploadItemStatus.SUCCESS,
                "message": "",
                "menuItemId": result.id,
            }
        )
        batch.set(item_ref, item_doc)
        batch.update(
            job_ref, {"successCount": firestore.Increment(1), "_updatedAt": now}
        )
        batch.update(
            restaurant_ref, {"metrics.totalItemsUploadedToday": firestore.Increment(1)}
        )
        batch.commit()
        return CsvRowProcessingOutcome.SUCCESS
