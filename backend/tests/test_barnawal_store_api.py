"""Core API regression tests for customer + admin grocery app flows."""

import os
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv


load_dotenv("/app/frontend/.env")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def test_state():
    return {}


# Store + catalog seed validations
def test_store_info_and_contacts(base_url, api_client):
    response = api_client.get(f"{base_url}/api/store", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "BARNAWAL PROVISION STORE"
    assert "8381869505" in data["contacts"] and "8858351010" in data["contacts"]
    assert "30" in data["delivery_message"]


def test_categories_seeded(base_url, api_client):
    response = api_client.get(f"{base_url}/api/categories", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 20
    assert all("name" in item and "product_count" in item for item in data[:3])


def test_products_seeded_searchable_and_fields(base_url, api_client, test_state):
    response = api_client.get(f"{base_url}/api/products", params={"q": "Tea", "limit": 20}, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    first = data["items"][0]
    assert first["selling_price"] <= first["mrp"]
    assert isinstance(first["stock_quantity"], int)
    assert isinstance(first["hindi_name"], str) and len(first["hindi_name"]) > 0
    test_state["product_id"] = first["id"]


def test_product_detail_contains_delivery_badge_data(base_url, api_client, test_state):
    product_id = test_state.get("product_id")
    if not product_id:
        pytest.skip("No product id from product list test")
    response = api_client.get(f"{base_url}/api/products/{product_id}", timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["product"]["id"] == product_id
    assert "delivery" in data["delivery_message"].lower()


# Customer auth + checkout flow validations
def test_demo_otp_request_returns_visible_demo_otp(base_url, api_client):
    payload = {"identifier": f"test-user-{int(time.time())}@mail.com"}
    response = api_client.post(f"{base_url}/api/auth/request-otp", json=payload, timeout=30)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Demo OTP generated"
    assert isinstance(data["demo_otp"], str) and len(data["demo_otp"]) >= 4


def test_customer_signup_login_and_profile(base_url, api_client, test_state):
    unique = f"TEST_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    mobile = f"9{str(int(time.time()))[-9:]}"
    email = f"{unique.lower()}@mail.com"
    password = "testpass123"

    signup_payload = {
        "full_name": unique,
        "mobile": mobile,
        "email": email,
        "password": password,
        "confirm_password": password,
    }
    signup_response = api_client.post(f"{base_url}/api/auth/signup", json=signup_payload, timeout=30)
    assert signup_response.status_code == 200
    signup_data = signup_response.json()
    assert signup_data["user"]["email"] == email
    assert signup_data["user"]["mobile"].endswith(mobile[-10:])
    assert isinstance(signup_data["token"], str) and len(signup_data["token"]) > 20

    login_payload = {"identifier": email, "password": password}
    login_response = api_client.post(f"{base_url}/api/auth/login", json=login_payload, timeout=30)
    assert login_response.status_code == 200
    login_data = login_response.json()
    token = login_data["token"]
    test_state["customer_token"] = token

    me_response = api_client.get(
        f"{base_url}/api/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["role"] == "customer"


def test_customer_address_order_and_history(base_url, api_client, test_state):
    token = test_state.get("customer_token")
    product_id = test_state.get("product_id")
    if not token or not product_id:
        pytest.skip("Missing customer token or product id")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    address = {
        "label": "Home",
        "house": "12A",
        "area": "TEST Colony",
        "city": "Ghazipur",
        "pincode": "233001",
        "landmark": "Near Market",
    }
    addr_response = api_client.post(f"{base_url}/api/me/addresses", json=address, headers=headers, timeout=30)
    assert addr_response.status_code == 200
    assert addr_response.json()["address"]["house"] == "12A"

    detail_response = api_client.get(f"{base_url}/api/products/{product_id}", timeout=30)
    assert detail_response.status_code == 200
    product = detail_response.json()["product"]

    order_payload = {
        "items": [
            {
                "product_id": product["id"],
                "product_name": product["product_name"],
                "variant": product["variant"],
                "quantity": 1,
                "selling_price": product["selling_price"],
                "image": product.get("product_image", ""),
            }
        ],
        "address": address,
        "coupon_code": "BGS25",
    }
    create_order = api_client.post(f"{base_url}/api/orders", json=order_payload, headers=headers, timeout=30)
    assert create_order.status_code == 200
    order_data = create_order.json()["order"]
    assert order_data["payment_method"] == "Cash on Delivery"
    assert "Pay when your order is delivered" in order_data["payment_note"]
    test_state["order_id"] = order_data["id"]

    orders_response = api_client.get(f"{base_url}/api/orders", headers=headers, timeout=30)
    assert orders_response.status_code == 200
    orders = orders_response.json()
    ids = [o["id"] for o in orders]
    assert order_data["id"] in ids


# Admin flow validations (login + dashboard + product + inventory + order status)
def test_admin_login_and_dashboard_counts(base_url, api_client, test_state):
    response = api_client.post(
        f"{base_url}/api/auth/admin-login",
        json={"mobile": "8381869505", "password": "admin123"},
        timeout=30,
    )
    assert response.status_code == 200
    data = response.json()
    token = data["token"]
    test_state["admin_token"] = token
    assert data["user"]["role"] in ["super_admin", "store_admin", "staff"]

    dash_response = api_client.get(
        f"{base_url}/api/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    assert dash_response.status_code == 200
    kpis = dash_response.json()["kpis"]
    assert kpis["total_products"] >= 400
    assert kpis["total_categories"] >= 20


def test_admin_product_add_inventory_adjust_and_delete(base_url, api_client, test_state):
    token = test_state.get("admin_token")
    if not token:
        pytest.skip("Missing admin token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    name = f"TEST_API_PRODUCT_{int(time.time())}"
    create_payload = {
        "product_name": name,
        "hindi_name": "टेस्ट प्रोडक्ट",
        "english_name": name,
        "category": "Tea",
        "subcategory": "General",
        "brand": "TEST",
        "variant": "1pc",
        "unit": "pc",
        "mrp": 99,
        "selling_price": 89,
        "stock_quantity": 10,
        "product_image": "",
        "description": "Test product",
        "status": "active",
    }
    create_response = api_client.post(f"{base_url}/api/admin/products", json=create_payload, headers=headers, timeout=30)
    assert create_response.status_code == 200
    product = create_response.json()["product"]
    pid = product["id"]
    test_state["created_admin_product_id"] = pid
    assert product["product_name"] == name

    inv_response = api_client.post(
        f"{base_url}/api/admin/inventory/adjust",
        json={"product_id": pid, "change_type": "stock_in", "quantity": 5, "note": "pytest stock in"},
        headers=headers,
        timeout=30,
    )
    assert inv_response.status_code == 200
    assert inv_response.json()["log"]["change_type"] == "stock_in"

    products_response = api_client.get(
        f"{base_url}/api/admin/products",
        params={"q": name, "limit": 500},
        headers=headers,
        timeout=30,
    )
    assert products_response.status_code == 200
    match = next((x for x in products_response.json()["items"] if x["id"] == pid), None)
    assert match is not None and match["stock_quantity"] >= 15

    delete_response = api_client.delete(f"{base_url}/api/admin/products/{pid}", headers=headers, timeout=30)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Product deleted"


def test_admin_order_status_update_if_order_exists(base_url, api_client, test_state):
    token = test_state.get("admin_token")
    order_id = test_state.get("order_id")
    if not token or not order_id:
        pytest.skip("Missing admin token or order id")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = api_client.put(
        f"{base_url}/api/admin/orders/{order_id}/status",
        json={"status": "Packed"},
        headers=headers,
        timeout=30,
    )
    assert response.status_code == 200
    order = response.json()["order"]
    assert order["status"] == "Packed"
    assert any(track["status"] == "Packed" for track in order.get("tracking", []))
