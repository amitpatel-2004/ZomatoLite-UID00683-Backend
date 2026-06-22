import unittest
import unittest.mock as mock
from http import HTTPStatus

from app import create_app
from app.constants import RESPONSE_MSG_FORBIDDEN, RESPONSE_MSG_MISSING_FIELDS
from app.restaurants.exceptions import (
    MenuItemNotFoundError,
    NotRestaurantOwnerError,
    RestaurantNotFoundError,
)
from tests.restaurants.test_data import (
    get_mock_menu_item_response,
    get_mock_restaurant_response,
    get_valid_create_menu_item_payload,
    get_valid_create_restaurant_payload,
)

OWNER_TOKEN = "Bearer owner-fake-token"
CUSTOMER_TOKEN = "Bearer customer-fake-token"
RESTAURANT_ID = "rest-123"
ITEM_ID = "item-123"

PAGINATED_RESTAURANTS = {
    "items": [get_mock_restaurant_response().model_dump(by_alias=True)],
    "page": 1,
    "hasMore": False,
}

PAGINATED_MENU_ITEMS = {
    "items": [get_mock_menu_item_response().model_dump(by_alias=True)],
    "page": 1,
    "hasMore": False,
}


def _mock_owner_auth(mock_verify):
    mock_verify.return_value = {"uid": "owner-uid-123", "role": "owner"}


def _mock_customer_auth(mock_verify):
    mock_verify.return_value = {"uid": "customer-uid-456", "role": "customer"}


class TestRestaurantListView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/restaurants/"

    @mock.patch("app.restaurants.views.restaurant_service.list_restaurants")
    def test_returns_200_with_paginated_restaurants(self, mock_list):
        mock_list.return_value = PAGINATED_RESTAURANTS
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = response.get_json()
        self.assertEqual(body["message"], "Restaurants fetched successfully.")
        self.assertIn("items", body["data"])
        self.assertIn("hasMore", body["data"])


class TestRestaurantCreateView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = "/api/v1/restaurants/"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.create_restaurant")
    def test_returns_201_for_owner(self, mock_create, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_create.return_value = get_mock_restaurant_response()

        response = self.client.post(
            self.url,
            json=get_valid_create_restaurant_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(
            response.get_json()["message"], "Restaurant created successfully."
        )

    def test_returns_401_without_token(self):
        response = self.client.post(
            self.url, json=get_valid_create_restaurant_payload()
        )
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
        response = self.client.post(
            self.url, json={}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_MISSING_FIELDS)


class TestRestaurantDetailView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @mock.patch("app.restaurants.views.restaurant_service.get_restaurant")
    def test_returns_200_for_existing_restaurant(self, mock_get):
        mock_get.return_value = get_mock_restaurant_response()
        response = self.client.get(f"/api/v1/restaurants/{RESTAURANT_ID}")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    @mock.patch("app.restaurants.views.restaurant_service.get_restaurant")
    def test_returns_404_for_missing_restaurant(self, mock_get):
        mock_get.side_effect = RestaurantNotFoundError()
        response = self.client.get(f"/api/v1/restaurants/{RESTAURANT_ID}")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.get_json()["message"], "Restaurant not found.")


class TestRestaurantUpdateView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.update_restaurant")
    def test_returns_403_when_not_owner(self, mock_update, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_update.side_effect = NotRestaurantOwnerError()
        response = self.client.put(
            self.url, json={"name": "New Name"}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.get_json()["message"], RESPONSE_MSG_FORBIDDEN)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.update_restaurant")
    def test_returns_200_on_success(self, mock_update, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_update.return_value = get_mock_restaurant_response()
        response = self.client.put(
            self.url, json={"name": "New Name"}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.get_json()["message"], "Restaurant updated successfully."
        )


class TestRestaurantDeleteView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.delete_restaurant")
    def test_returns_200_on_success(self, mock_delete, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_delete.return_value = None
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.get_json()["message"], "Restaurant deleted successfully."
        )

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.delete_restaurant")
    def test_returns_404_when_not_found(self, mock_delete, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_delete.side_effect = RestaurantNotFoundError()
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestMenuItemListView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items"

    @mock.patch("app.restaurants.views.restaurant_service.list_menu_items")
    def test_returns_200_with_paginated_items(self, mock_list):
        mock_list.return_value = PAGINATED_MENU_ITEMS
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        body = response.get_json()
        self.assertEqual(body["message"], "Menu items fetched successfully.")
        self.assertIn("items", body["data"])

    @mock.patch("app.restaurants.views.restaurant_service.list_menu_items")
    def test_returns_404_when_restaurant_not_found(self, mock_list):
        mock_list.side_effect = RestaurantNotFoundError()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestMenuItemCreateView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.add_menu_item")
    def test_returns_201_on_success(self, mock_add, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_add.return_value = get_mock_menu_item_response()
        response = self.client.post(
            self.url,
            json=get_valid_create_menu_item_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertEqual(
            response.get_json()["message"], "Menu item added successfully."
        )

    def test_returns_401_without_token(self):
        response = self.client.post(self.url, json=get_valid_create_menu_item_payload())
        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.add_menu_item")
    def test_returns_400_for_missing_required_fields(self, _mock_add, mock_verify):
        _mock_owner_auth(mock_verify)
        response = self.client.post(
            self.url, json={}, headers={"Authorization": OWNER_TOKEN}
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.add_menu_item")
    def test_returns_403_when_not_owner(self, mock_add, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_add.side_effect = NotRestaurantOwnerError()
        response = self.client.post(
            self.url,
            json=get_valid_create_menu_item_payload(),
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)


class TestMenuItemDeleteView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items/{ITEM_ID}"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.delete_menu_item")
    def test_returns_200_on_success(self, mock_delete, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_delete.return_value = None
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.get_json()["message"], "Menu item deleted successfully."
        )

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch("app.restaurants.views.restaurant_service.delete_menu_item")
    def test_returns_404_when_item_not_found(self, mock_delete, mock_verify):
        _mock_owner_auth(mock_verify)
        mock_delete.side_effect = MenuItemNotFoundError()
        response = self.client.delete(self.url, headers={"Authorization": OWNER_TOKEN})
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response.get_json()["message"], "Menu item not found.")


class TestMenuItemUploadUrlView(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.url = f"/api/v1/restaurants/{RESTAURANT_ID}/menu-items/upload-url"

    @mock.patch("app.auth.middleware.auth.verify_id_token")
    @mock.patch(
        "app.restaurants.views.restaurant_service.generate_menu_item_upload_url"
    )
    def test_returns_200_with_upload_url(self, mock_gen, mock_verify):
        from app.restaurants.dtos import UploadUrlResponseDTO

        _mock_owner_auth(mock_verify)
        mock_gen.return_value = UploadUrlResponseDTO(
            upload_url="https://storage.googleapis.com/fake-signed-url",
            image_path="restaurants/rest-123/menu-items/123_img.jpg",
        )
        response = self.client.post(
            self.url,
            json={"fileName": "img.jpg", "contentType": "image/jpeg", "fileSize": 1024},
            headers={"Authorization": OWNER_TOKEN},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.get_json()["message"], "Upload URL generated successfully."
        )
        self.assertIn("uploadUrl", response.get_json()["data"])
