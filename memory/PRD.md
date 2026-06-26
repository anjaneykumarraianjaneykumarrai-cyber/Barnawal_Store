# BARNAWAL GENERAL STORE APP PRD

## Original Problem Statement
Build a Blinkit-style grocery and general store app for BARNAWAL GENERAL STORE with customer app, admin dashboard, COD-only checkout, 30-minute delivery messaging, authentication, seeded product catalogue, inventory, order, customer, delivery, reporting and settings management.

## Architecture Decisions
- Frontend: React JavaScript, Tailwind/shadcn-compatible styling, responsive dark green Blinkit-style UI.
- Backend: FastAPI with MongoDB using existing workspace environment variables.
- Authentication: JWT role-based access for customers and admins.
- Payments: Cash on Delivery only; UPI/cards/wallet/net banking disabled.
- OTP: MOCKED demo OTP displayed on screen for testing.
- Product media: category/product image URLs with local SVG fallback placeholders.

## User Personas
- Customer: browses products, searches categories, adds to cart, checks out via COD, tracks orders, manages profile/wishlist.
- Store Admin: manages dashboard KPIs, products, categories, inventory, orders, customers, delivery, reports and settings.
- Staff: can access admin workflows through role-based admin login.

## Core Requirements
- Show BARNAWAL GENERAL STORE name and contacts 8381869505 / 8858351010.
- Show “Delivery in 30 Minutes” on Home, Product, Cart and Checkout.
- COD-only checkout with “Pay when your order is delivered.”
- Seed all provided categories/products with variants, SKU, barcode, prices, stock, GST/status fields.
- Customer auth, wishlist, cart, checkout, orders, profile and notifications.
- Admin dashboard, product/category/inventory/order/customer/delivery/reports/settings screens.
- Mobile responsive layout and dark mode green theme.

## Implemented — 2026-06-23
- Built full customer storefront with splash, home, categories, search, products, product details, wishlist, cart, checkout, orders and profile.
- Built admin dashboard with KPI cards, chart, products, categories, inventory, orders, customers, delivery, reports and settings.
- Implemented FastAPI REST APIs, MongoDB seeding for 436 products across 21 categories, JWT auth, default admins and inventory/order flows.
- Verified COD-only behavior and 30-minute delivery messaging across required pages.
- Added backend regression tests: /app/backend/tests/test_barnawal_store_api.py, passing 10/10.

## Prioritized Backlog
### P0 Remaining
- None for current MVP core flow.

### P1 Remaining
- Replace MOCKED demo OTP with real SMS provider.
- Connect real image upload/storage for admin product images.
- Implement actual PDF/Excel export file generation.

### P2 Remaining
- Add advanced coupon rules, GST invoice PDF download, barcode scanner camera workflow, customer review moderation and richer analytics filters.

## Next Tasks
1. Add real SMS OTP provider when credentials are available.
2. Add file storage for product image uploads.
3. Implement PDF/Excel exports for reports and invoices.
4. Improve catalogue pricing/stock data with real store values.


## Implemented — 2026-06-23 Catalogue Expansion
- Added 11 new categories: Flour & Millets, Sugar & Sweeteners, Cooking Oils, Fasting Items, Besan & Sattu, Dry Fruits & Seeds, Whole Spices, Dalia & Grains, Pulses & Lentils, Pujan Materials, Puja Essentials.
- Imported all requested products and variants into MongoDB with SKU, barcode, pricing, stock, image, inventory log and Hindi category naming.
- Added idempotent catalogue migration so future seed updates add only missing products/categories without duplicating existing data.
- Verified totals: 616 products across 32 categories; regression tests pass 10/10.


## Implemented — 2026-06-23 Chocolates, Ayurveda & Category Navigation
- Added Chocolates & Sweets category with Cadbury 5 Star, Dairy Milk, Silk, KitKat, Munch, Milkybar, Snickers, Mars, Bounty, Amul chocolates, candies and more variants.
- Added Ayurveda & Juices category with Amla Juice, Aloe Vera Juice, Dabur Chyawanprash, Baidyanath/Zandu Chyawanprash and herbal juice/powder items.
- Updated customer category cards so clicking any category directly scrolls and opens that category’s products without needing the Shop Now button.
- Verified catalogue totals: 706 products across 34 categories; regression tests pass 10/10.


## Implemented — 2026-06-23 Admin Price & Item Folder
- Added a dedicated admin sidebar folder: Price & Items.
- Admin can update item MRP, selling price, stock quantity and status directly from product cards.
- Admin can add new products from the same folder and delete products from customer visibility.
- Customer product APIs now hide deleted and inactive products, while admin can still see/manage inactive products.
- Verified admin UI loads and regression tests pass 10/10.


## Implemented — 2026-06-23 Breakfast Image Update
- Added uploaded Kellogg's Chocos image to the Breakfast category.
- Updated Kellogg's Chocos 200g and 500g product cards to use the uploaded product image.
- Marked Kellogg's Chocos products as featured/best-seller so they appear prominently in Breakfast/customer listings.
- Verified via API and storefront screenshot.


## Implemented — 2026-06-23 Product Catalogue Images
- Generated 706 unique optimized SVG product images for all active products.
- Updated product_image for every product without changing product names, variants, categories, prices or stock.
- Category front images now use matching generated product images for consistent ecommerce presentation.
- Product cards were adjusted to show white-background product images on top, product name below, and price/add-to-cart below.
- Note: These are MOCKED generated clean catalogue illustrations until exact brand/product photos are uploaded.
- Verified via API, frontend screenshot and regression tests pass 10/10.


## Corrected — 2026-06-23 Real Uploaded Product Chart Images
- Replaced generated placeholders with real cropped images from the user's uploaded product chart for visible matching products.
- Real chart crops are now applied to matching Pulses & Lentils, Dry Fruits & Seeds, Sugar & Sweeteners, Cooking Oils, Biscuits and Hair Oils items.
- Restored the user's real Kellogg's Chocos uploaded photo for Breakfast/Kellogg's Chocos products.
- Corrected wrong cross-category matches, e.g. Rajma Masala now no longer uses Rajma pulse crop.
- Current real chart image coverage: 100 products from the uploaded chart plus 2 Kellogg's Chocos real product photos; remaining products keep generated catalogue illustrations until exact real photos are uploaded.


## Implemented — 2026-06-24 WhatsApp Direct Ordering
- Added WhatsApp Order buttons for customers who need help ordering directly.
- Added WhatsApp button in the header, home hero, floating quick-action button, and cart summary.
- Cart WhatsApp button auto-fills the customer's cart items, quantities, total, COD payment, and 30-minute delivery message.
- WhatsApp orders are sent to store number 8381869505.
- Verified visually and lint/regression tests pass 10/10.


## Implemented — 2026-06-25 Detailed Checkout + Admin Order Notifications
- Customer checkout now collects Name, Mobile, Email, House/Flat, Area, City, Pincode, Landmark before placing the COD order.
- Removed login requirement at checkout — guests can place orders directly with their details.
- New backend endpoint `POST /api/orders` accepts a `customer` object and address; validates required fields; stores `is_guest`, `email`, `mobile`, `customer_name`, full address with landmark on the order.
- Every new order also writes an entry to `db.admin_notifications` (title + customer + total + order_no).
- New admin endpoints: `GET /api/admin/notifications`, `PUT /api/admin/notifications/{id}/read`, `PUT /api/admin/notifications/read-all`.
- Admin dashboard at `/admin` now shows a bell icon in the topbar with an unread badge, polls every 8s, plays a sound + toast on new orders, and exposes a dropdown listing notifications.
- Admin Orders table shows order_no, customer_name, mobile, email, total, status, with a "View" button opening a modal containing full customer details (name/mobile/email), delivery address (house/area/city/pincode/landmark), itemised bill and status select.
- Test credentials: admin login 8381869505 / admin123 (seeded).
- Verified: backend pytest 4/4 pass; frontend testing passed; guest checkout, admin login, notifications and order detail modal all functional.

### Next Tasks / Backlog
- Optional: integrate Resend email notification for new orders (user opted to skip for now).
- Optional: real-time WebSocket admin notifications (currently 8s polling).
- Optional: assign delivery boy and SMS customer when order moves to Out For Delivery.


## Implemented — 2026-06-25 Delivery Boy Assignment + SMS (MOCKED)
- Added full delivery-boy CRUD (name, mobile, vehicle, status) in Admin → Delivery tab with grid, edit/delete and uniqueness on mobile.
- Active-orders list in Delivery tab with dropdowns to assign a delivery boy and change order status.
- `PUT /api/admin/orders/{id}/status` now accepts an optional `delivery_boy_id`; sets boy details on the order and writes a MOCKED SMS log entry every time status changes.
- `PUT /api/admin/orders/{id}/assign` assigns a delivery boy without changing status.
- When status changes to **Out For Delivery**, the SMS message includes order no., total, delivery partner's name + mobile + vehicle.
- `GET /api/admin/sms-logs?order_id=` lists all SMS logs; admin Delivery tab shows them in a panel.
- Order Detail modal now shows the assigned Delivery Partner (or "Not assigned yet" hint).
- SMS provider is **MOCKED** (writes to `db.sms_logs` and `logger.info`) — ready to swap with Twilio when keys are supplied.
- Verified: backend pytest 14/14 ✅, regression notifications 4/4 ✅, frontend testing 95% ✅, no blocking issues.


## Implemented — 2026-06-25 Price Sync (CSV + Bulk Edit)
- New admin sidebar **Price Sync** with three sections:
  1. CSV: download template CSV (`product_name, variant, brand, category, mrp, selling_price`) → fill from any source (Blinkit/Zepto/manual) → upload → backend matches by `english_name+variant`, updates only `mrp/selling_price/discount_percent/best_price/price_updated_at`.
  2. Bulk Edit Grid: filter by search + category, edit MRP/Selling Price inline, save in batch.
  3. Sync History: paginated log of every sync run (source, counts, performed_by).
- New backend endpoints (admin-only): `GET /admin/price-sync/template`, `POST /admin/price-sync/csv` (multipart), `POST /admin/price-sync/bulk-edit`, `GET /admin/price-sync/logs`, `GET /admin/price-sync/logs/{id}`.
- Validation enforced: missing fields, non-numeric prices, selling > MRP, duplicate rows, brand mismatch → row reported in `unmatched`/`skipped`, never silently dropped.
- Protected fields (product_name, category, images, stock, SKU, barcode, description) are **never** touched.
- Dashboard now shows a **Last Price Sync** card with timestamp, source and updated/unmatched/skipped counts.
- Customer **ProductCard** + **ProductDetail** show discount % and a **Best Price** badge for products with ≥20% off or `best_price=true`.
- About Blinkit live scraping: NOT implemented — would violate Blinkit ToS and break frequently. Users supply prices via CSV/UI (option D agreed with user).
- Verified: backend pytest 8/8, frontend 100% (testing_agent_v3 iteration_4.json), no critical or design issues.

## Restored — 2026-01 Preview Setup
- Restored uploaded grocery app codebase (backend FastAPI + frontend React) into /app workspace.
- Installed Python and Yarn dependencies; generated JWT_SECRET in /app/backend/.env.
- Backend, frontend, and MongoDB services all running via supervisor.
- Verified customer storefront (https://...preview.../) loads with 34 categories and 703+ seeded products.
- Verified /admin login works with mobile 8381869505 / password admin123 — Admin dashboard shows KPIs, sales chart, top-selling products.
