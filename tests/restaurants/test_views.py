import unittest
import unittest.mock as mock
from datetime import datetime
from http import HTTPStatus

from app import create_app
from app.constants import RESPONSE_MSG_FORBIDDEN, RESPONSE_MSG_MISSING_FIELDS
from app.restaurants.constants import (
    RESPONSE_MSG_MENU_ITEM_ADDED,
    RESPONSE_MSG_MENU_ITEM_DELETED,
    RESPONSE_MSG_MENU_ITEM_NOT_FOUND,
    RESPONSE_MSG_MENU_ITEMS_FETCHED,
    RESPONSE_MSG_RESTAURANT_CREATED,
    RESPONSE_MSG_RESTAURANT_DELETED,
    RESPONSE_MSG_RESTAURANT_NOT_FOUND,
    RESPONSE_MSG_RESTAURANT_UPDATED,
    RESPONSE_MSG_RESTAURANTS_FETCHED,
    RESPONSE_MSG_UPLOAD_URL_GENERATED,
)
from tests.restaurants.test_data import (
    get_mock_firestore_restaurant_doc,
    get_valid_create_menu_item_payload,
    get_valid_create_restaurant_payload,
)

OWNER_UID = "owner-uid-123"
RESTAURANT_ID = "rest-123"
ITEM_ID = "item-123"
OWNER_TOKEN = "Bearer owner-fake-token"
CUSTOMER_TOKEN = "Bearer customer-fake-token"


def _mock_owner_auth(mock_verify):
    mock_verify.return_value = {"uid": OWNER_UID, "role": "owner"}


def _mock_customer_auth(mock_verify):
    mock_verify.return_value = {"uid": "customer-uid-456", "role": "customer"}


def _make_firestore_snapshot(data: dict | None, exists: bool = True):
    snapshot = mock.MagicMock()
    snapshot.exists = exists
    snapshot.to_dict.return_value = data
    return snapshot


class TestRestaurantListView(unittest.TestCase):
    """Integration tests for GET /api/v1/restaurants."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/restaurants"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_with_paginated_restaurants(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_doc = mock.MagicMock()
        mock_doc.to_dict.return_value = get_mock_firestore_restaurant_doc(OWNER_UID)
        mock_fs.collection.return_value.where.return_value.order_by.return_value.limit.return_value.get.return_value = [mock_doc]

        response = self.client.get(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_RESTAURANTS_FETCHED)


class TestRestaurantCreateView(unittest.TestCase):
    """Integration tests for POST /api/v1/restaurants."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/restaurants"

    def test_returns_401_without_token(self):
        response = self.client.post(self.url, json=get_valid_create_restaurant_payload())
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_returns_403_for_customer(self, mock_verify):
        _mock_customer_auth(mock_verify)
        response = self.client.post(
            self.url,
            json=get_valid_create_restaurant_payload(),
            headers={"Authorization": CUSTOMER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_returns_400_for_missing_fields(self, mock_verify):
        _mock_owner_auth(mock_verify)
        response = self.client.post(self.url, json={}, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MISSING_FIELDS)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_201_for_owner(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_doc_ref = mock.MagicMock()
        mock_doc_ref.id = RESTAURANT_ID
        mock_fs.collection.return_value.document.return_value = mock_doc_ref

        response = self.client.post(
            self.url,
            json=get_valid_create_restaurant_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_RESTAURANT_CREATED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_firestore_document_saved_with_correct_fields(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_doc_ref = mock.MagicMock()
        mock_doc_ref.id = RESTAURANT_ID
        mock_fs.collection.return_value.document.return_value = mock_doc_ref

        self.client.post(
            self.url,
            json=get_valid_create_restaurant_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )

        mock_doc_ref.set.assert_called_once()
        written = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(written["ownerId"], OWNER_UID)
        self.assertEqual(written["name"], "Test Restaurant")
        self.assertEqual(written["status"], "active")
        self.assertIsInstance(written["_createdAt"], datetime)


class TestRestaurantDetailView(unittest.TestCase):
    """Integration tests for GET /api/v1/restaurants/<restaurant_id>."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_for_existing_restaurant(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        response = self.client.get(
            f"/api/v1/restaurants/{RESTAURANT_ID}",
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_404_for_missing_restaurant(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(None, exists=False)
        )
        response = self.client.get(
            f"/api/v1/restaurants/{RESTAURANT_ID}",
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_RESTAURANT_NOT_FOUND)


class TestRestaurantUpdateView(unittest.TestCase):
    """Integration tests for PUT /api/v1/restaurants/<restaurant_id>."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_on_success(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        response = self.client.put(
            self.url, json={"name": "New Name"}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_RESTAURANT_UPDATED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_403_when_not_owner(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc("different-owner-uid"))
        )
        response = self.client.put(
            self.url, json={"name": "New Name"}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_FORBIDDEN)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_updates_only_provided_fields(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )

        self.client.put(
            self.url, json={"name": "New Name"}, headers={"Authorization": OWNER_TOKEN}
        )

        mock_fs.document.return_value.set.assert_called_once()
        updates = mock_fs.document.return_value.set.call_args[0][0]
        self.assertEqual(updates["name"], "New Name")
        self.assertNotIn("cuisineTypes", updates)


class TestRestaurantDeleteView(unittest.TestCase):
    """Integration tests for DELETE /api/v1/restaurants/<restaurant_id>."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_on_success(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_RESTAURANT_DELETED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_404_when_not_found(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(None, exists=False)
        )
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_soft_deletes_by_setting_status_deleted(self, mock_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )

        self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})

        mock_fs.document.return_value.update.assert_called_once()
        updates = mock_fs.document.return_value.update.call_args[0][0]
        self.assertEqual(updates["status"], "deleted")


class TestMenuItemListView(unittest.TestCase):
    """Integration tests for GET /api/v1/restaurants/<restaurant_id>/menu-items."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.menu_items.service.FS_CLIENT")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_with_paginated_items(self, mock_resto_fs, mock_menu_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        mock_menu_fs.collection.return_value.where.return_value.order_by.return_value.limit.return_value.get.return_value = []

        response = self.client.get(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MENU_ITEMS_FETCHED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_404_when_restaurant_not_found(self, mock_resto_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(None, exists=False)
        )
        response = self.client.get(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestMenuItemCreateView(unittest.TestCase):
    """Integration tests for POST /api/v1/restaurants/<restaurant_id>/menu-items."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items"

    def test_returns_401_without_token(self):
        response = self.client.post(self.url, json=get_valid_create_menu_item_payload())
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    def test_returns_400_for_missing_required_fields(self, mock_verify):
        _mock_owner_auth(mock_verify)
        response = self.client.post(self.url, json={}, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_403_when_not_owner(self, mock_resto_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc("different-owner-uid"))
        )
        response = self.client.post(
            self.url,
            json=get_valid_create_menu_item_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.menu_items.service.FS_CLIENT")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_201_on_success(self, mock_resto_fs, mock_menu_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        mock_menu_fs.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        mock_menu_fs.collection.return_value.document.return_value.id = ITEM_ID

        response = self.client.post(
            self.url,
            json=get_valid_create_menu_item_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MENU_ITEM_ADDED)


class TestMenuItemDeleteView(unittest.TestCase):
    """Integration tests for DELETE /api/v1/restaurants/<restaurant_id>/menu-items/<item_id>."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items/{ITEM_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.menu_items.service.FS_CLIENT")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_on_success(self, mock_resto_fs, mock_menu_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        mock_menu_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot({"_id": ITEM_ID, "status": "active"})
        )

        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MENU_ITEM_DELETED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.menu_items.service.FS_CLIENT")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_404_when_item_not_found(self, mock_resto_fs, mock_menu_fs, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_resto_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        mock_menu_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(None, exists=False)
        )

        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MENU_ITEM_NOT_FOUND)


class TestMenuItemUploadUrlView(unittest.TestCase):
    """Handles POST /api/v1/restaurants/<restaurant_id>/menu-items/upload-url."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items/image-upload"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.menu_items.service.generate_signed_upload_url")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_200_with_upload_url(self, mock_fs, mock_generate_url, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_fs.document.return_value.get.return_value = (
            _make_firestore_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        )
        mock_generate_url.return_value = "https://storage.googleapis.com/fake-signed-url"

        response = self.client.post(
            self.url,
            json={"fileName": "img.jpg", "contentType": "image/jpeg", "fileSize": 1024},
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_UPLOAD_URL_GENERATED)
        self.assertIn("uploadUrl", response.get_json()["data"])
