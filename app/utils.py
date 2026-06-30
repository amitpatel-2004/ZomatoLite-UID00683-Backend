from datetime import timedelta
from http import HTTPStatus
from typing import Any, Callable

from flask import Request, Response, jsonify
from pydantic import ValidationError

from app.settings import IMAGE_UPLOAD_BUCKET_NAME, GCS_CLIENT


def extract_validation_errors(err: ValidationError) -> dict:
    return {str(e["loc"][0]): e["msg"] for e in err.errors()}


def parse_pagination_params(request: Request) -> tuple[str | None, int]:
    """Get cursor and limit from query params."""
    cursor = request.args.get("after", None)
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    limit = max(1, min(limit, 50))
    return cursor, limit


def build_paginated_response(items: list, next_cursor: str | None) -> dict:
    """Format the results into standardardized payload containing cursor metadata."""
    return {
        "items": items,
        "nextCursor": next_cursor,
        "hasMore": next_cursor is not None,
    }


def paginate_query(
    query,
    limit: int,
    mapper: Callable[[dict], dict],
    cursor_ref=None,
) -> dict[str, Any]:
    """Apply cursor, fetch docs, and return a paginated response dict."""
    if cursor_ref is not None:
        cursor_snap = cursor_ref.get()
        query = query.start_after(cursor_snap)
    docs = list(query.get())
    has_more = len(docs) > limit
    page_docs = docs[:limit]
    items = [mapper(doc.to_dict()) for doc in page_docs]
    next_cursor = page_docs[-1].id if has_more else None
    return build_paginated_response(items, next_cursor)


def json_response(
    message: str,
    data: Any = None,
    errors: dict[str, Any] | None = None,
    detail: str = "",
    status_code: HTTPStatus = HTTPStatus.OK,
) -> tuple[Response, HTTPStatus]:
    """Return a standardized JSON response tuple for Flask routes.

    Args:
        message: Description of the response status.
        data: Optional payload data.
        errors: Optional dictionary containing structured validation or system errors.
        detail: Optional detail about the error or result.
        status_code: HTTP status code (default: 200).

    Returns:
        Tuple of (Flask Response, int status code).
    """
    response_body: dict[str, Any] = {"message": message}

    if detail:
        response_body["detail"] = detail

    if data is not None:
        response_body["data"] = data

    if errors is not None:
        response_body["errors"] = errors

    return jsonify(response_body), status_code


def generate_signed_upload_url(
    object_path: str, content_type: str, expiry_minutes: int = 15
) -> str:
    """Generate a signed URL for client-side upload."""
    bucket = GCS_CLIENT.bucket(IMAGE_UPLOAD_BUCKET_NAME)
    blob = bucket.blob(object_path)
    return blob.generate_signed_url(
        expiration=timedelta(minutes=expiry_minutes),
        method="PUT",
        content_type=content_type,
        version="v4",
    )
