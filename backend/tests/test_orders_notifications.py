import os, uuid, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://quick-order-hub-37.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/admin-login", json={"mobile":"8381869505","password":"admin123"}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]

@pytest.fixture(scope="module")
def product():
    r = requests.get(f"{API}/products?limit=1", timeout=20)
    assert r.status_code == 200
    return r.json()["items"][0]

def test_guest_order_requires_customer(product):
    payload = {"items":[{"product_id":product["id"],"product_name":product["product_name"],"variant":product["variant"],"quantity":1,"selling_price":product["selling_price"]}],
               "address":{"house":"H1","area":"A1","city":"Ghazipur","pincode":"233001","landmark":""}}
    r = requests.post(f"{API}/orders", json=payload, timeout=20)
    assert r.status_code == 400

def test_guest_order_creates_and_notifies(product, admin_token):
    suffix = uuid.uuid4().hex[:6]
    payload = {"items":[{"product_id":product["id"],"product_name":product["product_name"],"variant":product["variant"],"quantity":2,"selling_price":product["selling_price"]}],
               "address":{"house":"H1","area":"A1","city":"Ghazipur","pincode":"233001","landmark":"Near park"},
               "customer":{"name":f"TEST_{suffix}","mobile":"9999988888","email":f"t_{suffix}@x.com"}}
    r = requests.post(f"{API}/orders", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    order = r.json()["order"]
    assert order["customer_name"].startswith("TEST_")
    assert order["mobile"] == "9999988888"
    assert order["payment_method"] == "Cash on Delivery"
    assert order["is_guest"] is True

    headers = {"Authorization": f"Bearer {admin_token}"}
    r = requests.get(f"{API}/admin/notifications", headers=headers, timeout=20)
    assert r.status_code == 200
    data = r.json()
    assert "unread_count" in data and "notifications" in data
    match = [n for n in data["notifications"] if n.get("order_id") == order["id"]]
    assert match, "notification not created"
    nid = match[0]["id"]

    r = requests.put(f"{API}/admin/notifications/{nid}/read", headers=headers, timeout=20)
    assert r.status_code == 200
    r = requests.put(f"{API}/admin/notifications/read-all", headers=headers, timeout=20)
    assert r.status_code == 200
    r = requests.get(f"{API}/admin/notifications", headers=headers, timeout=20)
    assert r.json()["unread_count"] == 0

def test_admin_notifications_requires_auth():
    r = requests.get(f"{API}/admin/notifications", timeout=20)
    assert r.status_code == 401

def test_admin_orders_lists_guest_order(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = requests.get(f"{API}/admin/orders", headers=headers, timeout=20)
    assert r.status_code == 200
    orders = r.json()
    assert isinstance(orders, list) and len(orders) > 0
    o = orders[0]
    for k in ["order_no","customer_name","mobile","email","total_amount","payment_method","status","address","items"]:
        assert k in o
