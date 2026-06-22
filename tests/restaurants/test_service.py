import unittest
import unittest.mock as mock

from app.restaurants.dtos import (
    CreateMenuItemPayloadDTO,
    CreateRestaurantPayloadDTO,
    UpdateRestaurantPayloadDTO,
)
from app.restaurants.exceptions import (
    NotRestaurantOwnerError,
    RestaurantNotFoundError,
)
from app.restaurants.service import RestaurantService
from app.enums import CuisineType
from tests.restaurants.test_data import get_mock_firestore_restaurant_doc

OWNER_UID = "owner-uid-123"
OTHER_UID = "other-uid-456"
RESTAURANT_ID = "rest-123"
ITEM_ID = "item-123"

service = RestaurantService()


def _make_snapshot(data: dict | None, exists: bool = True):
    snap = mock.MagicMock()
    snap.exists = exists
    snap.to_dict.return_value = data
    return snap


class TestCreateRestaurant(unittest.TestCase):

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_saves_correct_fields_and_returns_dto(self, mock_fs):
        mock_doc_ref = mock.MagicMock()
        mock_doc_ref.id = RESTAURANT_ID
        mock_fs.collection.return_value.document.return_value = mock_doc_ref

        payload = CreateRestaurantPayloadDTO(
            name="Test Restaurant",
            cuisine_types=[CuisineType.INDIAN],
            opening_time="09:00",
            closing_time="22:00",
        )
        result = service.create_restaurant(OWNER_UID, payload)

        mock_doc_ref.set.assert_called_once()
        written = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(written["ownerId"], OWNER_UID)
        self.assertEqual(written["name"], "Test Restaurant")
        self.assertEqual(written["status"], "active")
        self.assertEqual(result.id, RESTAURANT_ID)
        self.assertEqual(result.owner_id, OWNER_UID)


class TestGetRestaurant(unittest.TestCase):

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_raises_not_found_when_doc_missing(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(None, exists=False)

        with self.assertRaises(RestaurantNotFoundError):
            service.get_restaurant(RESTAURANT_ID)

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_dto_on_success(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )
        result = service.get_restaurant(RESTAURANT_ID)
        self.assertEqual(result.id, RESTAURANT_ID)


class TestUpdateRestaurant(unittest.TestCase):

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_raises_not_owner_error_for_wrong_uid(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )
        payload = UpdateRestaurantPayloadDTO(name="New Name")

        with self.assertRaises(NotRestaurantOwnerError):
            service.update_restaurant(OTHER_UID, RESTAURANT_ID, payload)

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_updates_only_provided_fields(self, mock_fs):
        doc_ref = mock.MagicMock()
        doc_ref.get.return_value = _make_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        mock_fs.collection.return_value.document.return_value = doc_ref

        payload = UpdateRestaurantPayloadDTO(name="New Name")
        result = service.update_restaurant(OWNER_UID, RESTAURANT_ID, payload)

        doc_ref.update.assert_called_once()
        updates = doc_ref.update.call_args[0][0]
        self.assertEqual(updates["name"], "New Name")
        self.assertNotIn("cuisineTypes", updates)
        self.assertEqual(result.name, "New Name")


class TestDeleteRestaurant(unittest.TestCase):

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_raises_not_owner_for_wrong_uid(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )

        with self.assertRaises(NotRestaurantOwnerError):
            service.delete_restaurant(OTHER_UID, RESTAURANT_ID)

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_soft_deletes_restaurant_for_correct_owner(self, mock_fs):
        doc_ref = mock.MagicMock()
        doc_ref.get.return_value = _make_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))
        mock_fs.collection.return_value.document.return_value = doc_ref

        service.delete_restaurant(OWNER_UID, RESTAURANT_ID)
        doc_ref.update.assert_called_once()
        updates = doc_ref.update.call_args[0][0]
        self.assertEqual(updates["status"], "deleted")


class TestAddMenuItem(unittest.TestCase):

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_adds_item_for_correct_owner(self, mock_fs):
        restaurant_ref = mock.MagicMock()
        restaurant_ref.get.return_value = _make_snapshot(get_mock_firestore_restaurant_doc(OWNER_UID))

        item_ref = mock.MagicMock()
        item_ref.id = ITEM_ID
        restaurant_ref.collection.return_value.document.return_value = item_ref

        mock_fs.collection.return_value.document.return_value = restaurant_ref

        payload = CreateMenuItemPayloadDTO(name="Butter Chicken", price=299.0, is_veg=False)
        result = service.add_menu_item(OWNER_UID, RESTAURANT_ID, payload)

        item_ref.set.assert_called_once()
        self.assertEqual(result.id, ITEM_ID)
        self.assertEqual(result.price, 299.0)

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_raises_not_owner_for_wrong_uid(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )

        payload = CreateMenuItemPayloadDTO(name="Item", price=100.0, is_veg=True)
        with self.assertRaises(NotRestaurantOwnerError):
            service.add_menu_item(OTHER_UID, RESTAURANT_ID, payload)


class TestGenerateUploadUrl(unittest.TestCase):

    @mock.patch("app.restaurants.service.generate_signed_upload_url")
    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_returns_correct_path_format(self, mock_fs, mock_gcs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )
        mock_gcs.return_value = "https://storage.googleapis.com/signed-url"

        result = service.generate_menu_item_upload_url(OWNER_UID, RESTAURANT_ID, "burger.jpg", "image/jpeg")

        self.assertIn(RESTAURANT_ID, result.image_path)
        self.assertIn("burger.jpg", result.image_path)
        self.assertEqual(result.upload_url, "https://storage.googleapis.com/signed-url")

    @mock.patch("app.restaurants.service.FS_CLIENT")
    def test_raises_not_owner_for_wrong_uid(self, mock_fs):
        mock_fs.collection.return_value.document.return_value.get.return_value = _make_snapshot(
            get_mock_firestore_restaurant_doc(OWNER_UID)
        )

        with self.assertRaises(NotRestaurantOwnerError):
            service.generate_menu_item_upload_url(OTHER_UID, RESTAURANT_ID, "img.jpg", "image/jpeg")
