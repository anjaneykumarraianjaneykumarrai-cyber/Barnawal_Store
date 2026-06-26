"""Backend tests for Blinkit Price Sync feature."""
import os
import io
import csv
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://quick-order-hub-37.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/admin-login", json={"mobile": "8381869505", "password": "admin123"}, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------------- TEMPLATE ----------------
class TestPriceSyncTemplate:
    def test_template_requires_admin(self):
        r = requests.get(f"{API}/admin/price-sync/template", timeout=30)
        assert r.status_code == 401

    def test_template_returns_csv(self, auth_headers):
        r = requests.get(f"{API}/admin/price-sync/template", headers=auth_headers, timeout=60)
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        rows = list(csv.reader(io.StringIO(r.text)))
        assert rows[0] == ["product_name", "variant", "brand", "category", "mrp", "selling_price"]
        assert len(rows) > 1


# ---------------- CSV UPLOAD ----------------
class TestPriceSyncCSV:
    def test_csv_full_roundtrip(self, auth_headers):
        # Download template
        r = requests.get(f"{API}/admin/price-sync/template", headers=auth_headers, timeout=60)
        rows = list(csv.reader(io.StringIO(r.text)))
        header, data_rows = rows[0], rows[1:]

        # Modify first 5 rows: drop selling by 25 (>=20% discount likely)
        sample = data_rows[:5]
        # ensure prices are numeric
        for row in sample:
            try:
                mrp = float(row[4])
            except Exception:
                row[4] = "100"
                mrp = 100
            new_selling = max(1, round(mrp * 0.75, 2))  # 25% off
            row[5] = str(new_selling)

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(header)
        w.writerows(sample)
        files = {"file": ("test_upload.csv", buf.getvalue(), "text/csv")}
        rr = requests.post(f"{API}/admin/price-sync/csv", headers=auth_headers, files=files, timeout=60)
        assert rr.status_code == 200, rr.text
        report = rr.json()["report"]
        assert report["matched_count"] == 5, f"Expected 5 matched, report={report}"
        assert report["unmatched_count"] == 0
        # Each matched item should be best_price (>=20%)
        for m in report["matched"]:
            assert m["discount_percent"] >= 20

        # Verify product persisted
        first = report["matched"][0]
        pr = requests.get(f"{API}/products/{first['product_id']}", timeout=30).json()["product"]
        assert pr["selling_price"] == first["new_selling_price"]
        assert pr["mrp"] == first["new_mrp"]
        assert pr.get("best_price") is True
        assert pr.get("discount_percent") >= 20
        assert "price_updated_at" in pr

    def test_csv_validation_errors(self, auth_headers):
        # build CSV with various bad rows
        csv_text = "product_name,variant,brand,category,mrp,selling_price\n"
        csv_text += ",,Generic,Tea,100,90\n"  # missing name+variant
        csv_text += "Tata Tea Premium,100g,Tata,Tea,abc,50\n"  # invalid number
        csv_text += "Tata Tea Premium,100g,Tata,Tea,100,150\n"  # selling > mrp
        csv_text += "Tata Tea Premium,100g,Tata,Tea,100,80\n"  # ok
        csv_text += "Tata Tea Premium,100g,Tata,Tea,100,80\n"  # duplicate
        csv_text += "Made Up Product,XXX,Generic,Tea,100,80\n"  # unmatched
        files = {"file": ("bad.csv", csv_text, "text/csv")}
        r = requests.post(f"{API}/admin/price-sync/csv", headers=auth_headers, files=files, timeout=60)
        assert r.status_code == 200, r.text
        report = r.json()["report"]
        skipped_reasons = [s["reason"] for s in report["skipped"]]
        assert any("Missing" in s for s in skipped_reasons)
        assert any("Invalid" in s for s in skipped_reasons)
        assert any("exceed" in s.lower() for s in skipped_reasons)
        assert any("duplicate" in s.lower() for s in skipped_reasons)
        assert report["unmatched_count"] >= 1
        assert report["matched_count"] >= 1

    def test_csv_does_not_modify_protected_fields(self, auth_headers):
        # Pick a product, snapshot, do bulk-edit, ensure protected fields unchanged
        prods = requests.get(f"{API}/admin/products?limit=1", headers=auth_headers, timeout=30).json()
        p = prods["items"][0]
        before = {k: p.get(k) for k in ["product_name", "category", "product_image", "stock_quantity", "sku", "barcode", "description"]}
        payload = {"items": [{"product_id": p["id"], "mrp": 200.0, "selling_price": 160.0}], "source": "test"}
        r = requests.post(f"{API}/admin/price-sync/bulk-edit", headers=auth_headers, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        after = requests.get(f"{API}/products/{p['id']}", timeout=30).json()["product"]
        for k, v in before.items():
            assert after[k] == v, f"Protected field {k} changed: {v} -> {after[k]}"
        assert after["mrp"] == 200.0
        assert after["selling_price"] == 160.0
        assert after["discount_percent"] == 20.0
        assert after["best_price"] is True


# ---------------- BULK EDIT ----------------
class TestBulkEdit:
    def test_bulk_edit_validation(self, auth_headers):
        prods = requests.get(f"{API}/admin/products?limit=2", headers=auth_headers, timeout=30).json()
        items = [
            {"product_id": prods["items"][0]["id"], "mrp": 100.0, "selling_price": 90.0},  # ok
            {"product_id": prods["items"][1]["id"], "mrp": 100.0, "selling_price": 200.0},  # selling>mrp
        ]
        r = requests.post(f"{API}/admin/price-sync/bulk-edit", headers=auth_headers, json={"items": items}, timeout=30)
        assert r.status_code == 200
        report = r.json()["report"]
        assert report["matched_count"] == 1
        assert report["skipped_count"] == 1


# ---------------- LOGS ----------------
class TestLogs:
    def test_logs_list_and_detail(self, auth_headers):
        r = requests.get(f"{API}/admin/price-sync/logs", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data and "last_sync" in data
        assert len(data["logs"]) > 0
        sync_id = data["logs"][0]["id"]
        d = requests.get(f"{API}/admin/price-sync/logs/{sync_id}", headers=auth_headers, timeout=30)
        assert d.status_code == 200
        full = d.json()
        assert "matched" in full and "unmatched" in full and "skipped" in full


# ---------------- DASHBOARD ----------------
class TestDashboard:
    def test_dashboard_includes_last_price_sync(self, auth_headers):
        r = requests.get(f"{API}/admin/dashboard", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert "last_price_sync" in body
        assert body["last_price_sync"] is not None
        assert "source" in body["last_price_sync"]
        assert "matched_count" in body["last_price_sync"]
