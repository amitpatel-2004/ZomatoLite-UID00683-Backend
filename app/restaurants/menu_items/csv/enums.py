from enum import Enum


class CsvUploadSuccessMessage(str, Enum):
    UPLOAD_URL_GENERATED = "Upload URL generated successfully."
    ROW_ALREADY_PROCESSED = "Row already processed."
    ROW_RECORDED_AS_FAILED = "Row recorded as failed."
    ROW_PROCESSED_SUCCESSFULLY = "Row processed successfully."


class CsvUploadErrorMessage(str, Enum):
    FILE_SIZE_EXCEEDS_LIMIT = "File size exceeds the allowed limit."


class CsvUploadJobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CsvUploadItemStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
