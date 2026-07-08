from enum import Enum


class InternalErrorMessage(str, Enum):
    RESPONSE_MSG_PUSH_TOKEN_MISSING = "Push authorization token is missing."
    RESPONSE_MSG_PUSH_TOKEN_INVALID = "Push authorization token is invalid."


class CsvRowProcessingOutcome(str, Enum):
    PROCESSED = "processed"
    SUCCESS = "success"
    FAILED = "failed"
