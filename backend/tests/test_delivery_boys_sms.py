"""Tests for delivery boys CRUD, order assignment, and mocked SMS logs."""
import os
import uuid
import requests
import pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE}/api"
TIMEOUT = 25


# -------- shared fixtures --------
@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{API}/auth/admin-login",
                      json={"mobile": "8381869505", "password": "admin123"}, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def product():
    r = requests.get(f"{API}/products?limit=1", timeout=TIMEOUT)
    assert r.status_code == 200
    return r.json()["items"][0]


@pytest.fixture(scope="module")
def guest_order(product):
    suffix = uuid.uuid4().hex[:6]
    payload = {
        "items": [{
            "product_id": product["id"],
            "product_name": product["product_name"],
            "variant": product["variant"],
            "quantity": 1,
            "selling_price": product["selling_price"],
        }],
        "address": {"house": "H1", "area": "A1", "city": "Ghazipur",
                    "pincode": "233001", "landmark": "TestLM"},
        "customer": {"name": f"TEST_{suffix}", "mobile": "9000011122",
                     "email": f"t_{suffix}@x.com"},
    }
    r = requests.post(f"{API}/orders", json=payload, timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    return r.json()["order"]


# -------- Delivery Boys CRUD --------
class TestDeliveryBoyCRUD:
    created_id = None
    mobile = None

    def test_requires_admin_auth(self):
        r = requests.get(f"{API}/admin/delivery-boys", timeout=TIMEOUT)
        assert r.status_code in (401, 403)

    def test_create_delivery_boy(self, admin_headers):
        TestDeliveryBoyCRUD.mobile = f"9{uuid.uuid4().int % 1000000000:09d}"
        payload = {"name": "TEST_Boy_A", "mobile": TestDeliveryBoyCRUD.mobile,
                   "vehicle": "UP65 AB 0001", "status": "active"}
        r = requests.post(f"{API}/admin/delivery-boys", headers=admin_headers,
                          json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["message"]
        boy = body["delivery_boy"]
        assert boy["name"] == "TEST_Boy_A"
        assert boy["mobile"] == TestDeliveryBoyCRUD.mobile
        assert boy["vehicle"] == "UP65 AB 0001"
        assert boy["status"] == "active"
        assert "id" in boy and isinstance(boy["id"], str)
        assert "_id" not in boy
        TestDeliveryBoyCRUD.created_id = boy["id"]

    def test_duplicate_mobile_rejected(self, admin_headers):
        r = requests.post(f"{API}/admin/delivery-boys", headers=admin_headers,
                          json={"name": "Dup", "mobile": TestDeliveryBoyCRUD.mobile,
                                "vehicle": "X", "status": "active"}, timeout=TIMEOUT)
        assert r.status_code == 409

    def test_list_delivery_boys(self, admin_headers):
        r = requests.get(f"{API}/admin/delivery-boys", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        boys = r.json()
        assert isinstance(boys, list)
        ids = [b["id"] for b in boys]
        assert TestDeliveryBoyCRUD.created_id in ids
        for b in boys:
            assert "_id" not in b

    def test_update_delivery_boy(self, admin_headers):
        update = {"name": "TEST_Boy_A_renamed", "mobile": TestDeliveryBoyCRUD.mobile,
                  "vehicle": "UP65 AB 9999", "status": "inactive"}
        r = requests.put(f"{API}/admin/delivery-boys/{TestDeliveryBoyCRUD.created_id}",
                         headers=admin_headers, json=update, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        boy = r.json()["delivery_boy"]
        assert boy["name"] == "TEST_Boy_A_renamed"
        assert boy["vehicle"] == "UP65 AB 9999"
        assert boy["status"] == "inactive"

        # GET-verify persistence
        r = requests.get(f"{API}/admin/delivery-boys", headers=admin_headers, timeout=TIMEOUT)
        match = [b for b in r.json() if b["id"] == TestDeliveryBoyCRUD.created_id]
        assert match and match[0]["name"] == "TEST_Boy_A_renamed"
        assert match[0]["status"] == "inactive"

    def test_update_not_found(self, admin_headers):
        r = requests.put(f"{API}/admin/delivery-boys/does-not-exist",
                         headers=admin_headers,
                         json={"name": "x", "mobile": "9111111111"}, timeout=TIMEOUT)
        assert r.status_code == 404

    def test_delete_delivery_boy(self, admin_headers):
        r = requests.delete(f"{API}/admin/delivery-boys/{TestDeliveryBoyCRUD.created_id}",
                            headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        r = requests.get(f"{API}/admin/delivery-boys", headers=admin_headers, timeout=TIMEOUT)
        ids = [b["id"] for b in r.json()]
        assert TestDeliveryBoyCRUD.created_id not in ids


# -------- Order assign + status with SMS --------
class TestOrderAssignAndSMS:
    boy_id = None
    boy_mobile = None
    boy_name = "TEST_Boy_SMS"

    @pytest.fixture(autouse=True, scope="class")
    def _create_boy(self, admin_headers, request):
        m = f"9{uuid.uuid4().int % 1000000000:09d}"
        r = requests.post(f"{API}/admin/delivery-boys", headers=admin_headers,
                          json={"name": TestOrderAssignAndSMS.boy_name, "mobile": m,
                                "vehicle": "UP65 SMS 0001", "status": "active"},
                          timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        TestOrderAssignAndSMS.boy_id = r.json()["delivery_boy"]["id"]
        TestOrderAssignAndSMS.boy_mobile = m

        def cleanup():
            requests.delete(f"{API}/admin/delivery-boys/{TestOrderAssignAndSMS.boy_id}",
                            headers=admin_headers, timeout=TIMEOUT)
        request.addfinalizer(cleanup)

    def test_status_change_without_boy_creates_sms(self, admin_headers, guest_order):
        r = requests.put(f"{API}/admin/orders/{guest_order['id']}/status",
                         headers=admin_headers,
                         json={"status": "Accepted"}, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["order"]["status"] == "Accepted"
        sms = body["sms_log"]
        assert sms["status"] == "Accepted"
        assert sms["provider"] == "MOCKED"
        assert sms["to_mobile"] == guest_order["mobile"]
        assert "Accepted" in sms["message"]

    def test_assign_without_status_change(self, admin_headers, guest_order):
        r = requests.put(f"{API}/admin/orders/{guest_order['id']}/assign",
                         headers=admin_headers,
                         json={"delivery_boy_id": TestOrderAssignAndSMS.boy_id},
                         timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        order = r.json()["order"]
        assert order["delivery_boy_id"] == TestOrderAssignAndSMS.boy_id
        assert order["delivery_boy_name"] == TestOrderAssignAndSMS.boy_name
        assert order["delivery_boy_mobile"] == TestOrderAssignAndSMS.boy_mobile
        # status should remain (not changed by assign)
        assert order["status"] in ("Accepted", "New Order")

    def test_assign_boy_not_found(self, admin_headers, guest_order):
        r = requests.put(f"{API}/admin/orders/{guest_order['id']}/assign",
                         headers=admin_headers,
                         json={"delivery_boy_id": "no-such-boy"}, timeout=TIMEOUT)
        assert r.status_code == 404

    def test_out_for_delivery_with_boy_detailed_sms(self, admin_headers, guest_order):
        r = requests.put(f"{API}/admin/orders/{guest_order['id']}/status",
                         headers=admin_headers,
                         json={"status": "Out For Delivery",
                               "delivery_boy_id": TestOrderAssignAndSMS.boy_id},
                         timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        body = r.json()
        order = body["order"]
        assert order["status"] == "Out For Delivery"
        assert order["delivery_boy_id"] == TestOrderAssignAndSMS.boy_id
        sms = body["sms_log"]
        assert sms["status"] == "Out For Delivery"
        msg = sms["message"]
        # Detailed SMS must contain boy name + mobile + OUT FOR DELIVERY + order_no
        assert TestOrderAssignAndSMS.boy_name in msg
        assert TestOrderAssignAndSMS.boy_mobile in msg
        assert "OUT FOR DELIVERY" in msg
        assert guest_order["order_no"] in msg

    def test_sms_logs_endpoint_lists_messages(self, admin_headers, guest_order):
        r = requests.get(f"{API}/admin/sms-logs", headers=admin_headers, timeout=TIMEOUT)
        assert r.status_code == 200
        logs = r.json()
        assert isinstance(logs, list)
        my = [l for l in logs if l.get("order_id") == guest_order["id"]]
        assert len(my) >= 2  # at least Accepted + Out For Delivery
        statuses = {l["status"] for l in my}
        assert "Out For Delivery" in statuses
        for l in my:
            assert "_id" not in l
            assert l["provider"] == "MOCKED"

    def test_sms_logs_filter_by_order(self, admin_headers, guest_order):
        r = requests.get(f"{API}/admin/sms-logs",
                         headers=admin_headers,
                         params={"order_id": guest_order["id"]}, timeout=TIMEOUT)
        assert r.status_code == 200
        logs = r.json()
        assert logs and all(l["order_id"] == guest_order["id"] for l in logs)

    def test_status_update_unknown_order(self, admin_headers):
        r = requests.put(f"{API}/admin/orders/nope/status",
                         headers=admin_headers,
                         json={"status": "Accepted"}, timeout=TIMEOUT)
        assert r.status_code == 404
