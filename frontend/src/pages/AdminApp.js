/* eslint-disable react/no-unstable-nested-components */
import { useEffect, useMemo, useRef, useState } from "react";
import { Bell, BarChart3, Boxes, FolderPen, RefreshCw, LayoutDashboard, LogOut, MessageCircle, PackageCheck, Search, Settings, ShoppingBag, Truck, Users, X } from "lucide-react";
import { toast } from "sonner";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import AuthPanel from "@/components/AuthPanel";
import { api, getUser, logout } from "@/lib/api";
import { fetchStore, readStore, writeStore as writeStoreSettings } from "@/lib/storeSettings";

// Build a wa.me link that opens WhatsApp with the message prefilled.
// Defaults to +91 (India) if mobile is 10 digits without country code.
function buildWhatsAppLink(mobile, message) {
  const digits = String(mobile || "").replace(/\D/g, "");
  const phone = digits.length === 10 ? `91${digits}` : digits;
  return `https://wa.me/${phone}?text=${encodeURIComponent(message || "")}`;
}

const menu = [
  ["dashboard", "Dashboard", LayoutDashboard], ["orders", "Orders", ShoppingBag], ["products", "Products", Boxes],
  ["price-items", "Price & Items", FolderPen],
  ["price-sync", "Price Sync", RefreshCw],
  ["categories", "Categories", PackageCheck], ["inventory", "Inventory", BarChart3], ["customers", "Customers", Users],
  ["delivery", "Delivery", Truck], ["reports", "Reports", BarChart3], ["settings", "Settings", Settings],
];

export default function AdminApp() {
  const [user, setUser] = useState(getUser("admin"));
  const [active, setActive] = useState("dashboard");
  const [store, setStore] = useState(readStore());
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [inventory, setInventory] = useState({ products: [], logs: [] });
  const [reports, setReports] = useState(null);
  const [deliveryBoys, setDeliveryBoys] = useState([]);
  const [smsLogs, setSmsLogs] = useState([]);
  const [boyForm, setBoyForm] = useState({ id: "", name: "", mobile: "", vehicle: "", status: "active" });
  const [q, setQ] = useState("");
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const prevUnreadRef = useRef(0);
  const audioRef = useRef(null);
  const [productForm, setProductForm] = useState({ product_name: "", hindi_name: "", category: "Tea", subcategory: "General", brand: "", variant: "1pc", unit: "pc", mrp: 50, selling_price: 45, stock_quantity: 20, product_image: "", description: "", status: "active" });
  const isAdmin = user && ["super_admin", "store_admin", "staff"].includes(user.role);

  const load = async () => {
    if (!isAdmin) return;
    try {
      const [dash, prods, cats, ords, cust, inv, reps, boys, sms] = await Promise.all([
        api.get("/admin/dashboard"), api.get("/admin/products", { params: { q, limit: 160 } }), api.get("/admin/categories"),
        api.get("/admin/orders"), api.get("/admin/customers"), api.get("/admin/inventory"), api.get("/admin/reports"),
        api.get("/admin/delivery-boys"), api.get("/admin/sms-logs"),
      ]);
      setDashboard(dash.data); setProducts(prods.data.items); setCategories(cats.data); setOrders(ords.data); setCustomers(cust.data); setInventory(inv.data); setReports(reps.data); setDeliveryBoys(boys.data); setSmsLogs(sms.data);
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        // Admin session expired/invalid — bail to login page.
        setUser(null);
      } else {
        // Silently swallow other errors; the polling will retry.
        // console.warn("admin load failed", err);
      }
    }
  };
  useEffect(() => { load(); }, [isAdmin, q]);

  useEffect(() => {
    const updateStore = () => setStore(readStore());
    window.addEventListener("store-settings-updated", updateStore);
    fetchStore().then(updateStore);
    return () => window.removeEventListener("store-settings-updated", updateStore);
  }, []);
  const storeContactsLine = (store.contacts || []).join(" / ");

  const loadNotifications = async () => {
    if (!isAdmin) return;
    try {
      const { data } = await api.get("/admin/notifications");
      setNotifications(data.notifications);
      const newUnread = data.unread_count;
      if (newUnread > prevUnreadRef.current && prevUnreadRef.current >= 0) {
        // Play sound + toast for new orders (skip first load)
        if (prevUnreadRef.current !== 0 || notifications.length > 0) {
          try { audioRef.current?.play().catch(() => {}); } catch (e) { /* ignore */ }
          const latest = data.notifications.find((n) => !n.is_read);
          if (latest) {
            const confirmationMsg = `Hi ${latest.customer_name}, ${store.name || "BARNAWAL GENERAL STORE"} has received your order ${latest.order_no} for ₹${latest.total_amount}. We are confirming your order and will deliver in ${store.delivery_time || "30 minutes"}. Pay on delivery. — ${storeContactsLine}`;
            const link = buildWhatsAppLink(latest.mobile, confirmationMsg);
            try { window.open(link, "_blank", "noopener"); } catch (e) { /* ignore */ }
            toast.success(`🔔 New Order: ${latest.order_no} from ${latest.customer_name}`, {
              description: `WhatsApp confirmation ready for ${latest.mobile}. Click below if the tab didn't open.`,
              action: { label: "Send WhatsApp", onClick: () => window.open(link, "_blank", "noopener") },
              duration: 10000,
            });
          }
          // Refresh orders/dashboard so admin sees the new order (errors are swallowed inside load())
          load();
        }
      }
      prevUnreadRef.current = newUnread;
      setUnreadCount(newUnread);
    } catch (err) {
      const status = err?.response?.status;
      if (status === 401 || status === 403) {
        setUser(null);
      }
      // otherwise silently ignore; next tick will retry
    }
  };
  useEffect(() => {
    if (!isAdmin) return undefined;
    loadNotifications();
    const interval = setInterval(loadNotifications, 8000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin]);

  const markAllRead = async () => {
    await api.put("/admin/notifications/read-all");
    loadNotifications();
  };
  const openOrderFromNotification = async (n) => {
    await api.put(`/admin/notifications/${n.id}/read`);
    const order = orders.find((o) => o.id === n.order_id);
    if (order) {
      setSelectedOrder(order);
      setActive("orders");
    }
    setShowNotifications(false);
    loadNotifications();
  };

  const addProduct = async (e) => {
    e.preventDefault();
    await api.post("/admin/products", productForm);
    toast.success("Product added");
    setProductForm({ ...productForm, product_name: "", hindi_name: "", brand: "", description: "" });
    load();
  };
  const deleteProduct = async (id) => { await api.delete(`/admin/products/${id}`); toast.success("Product deleted"); load(); };
  const updateProduct = async (product, updates) => {
    const payload = {
      product_name: product.product_name,
      hindi_name: product.hindi_name || "",
      english_name: product.english_name || product.product_name,
      category: product.category,
      subcategory: product.subcategory || "General",
      brand: product.brand || "Generic",
      variant: product.variant || "1pc",
      unit: product.unit || "pc",
      mrp: Number(updates.mrp ?? product.mrp),
      selling_price: Number(updates.selling_price ?? product.selling_price),
      stock_quantity: Number(updates.stock_quantity ?? product.stock_quantity),
      product_image: product.product_image || "",
      description: product.description || "",
      status: updates.status ?? product.status ?? "active",
    };
    await api.put(`/admin/products/${product.id}`, payload);
    toast.success("Item updated for customer app");
    load();
  };
  const updateOrder = async (id, status, deliveryBoyId) => {
    const payload = { status };
    if (deliveryBoyId) payload.delivery_boy_id = deliveryBoyId;
    const { data } = await api.put(`/admin/orders/${id}/status`, payload);
    if (data.sms_log) {
      const link = buildWhatsAppLink(data.sms_log.to_mobile, data.sms_log.message);
      // Auto-open WhatsApp tab so admin just clicks Send (popup permitted because admin click triggered this)
      try { window.open(link, "_blank", "noopener"); } catch (e) { /* ignore */ }
      toast.success(`Status updated → ${status}`, {
        description: `WhatsApp ready for ${data.sms_log.to_mobile}. Click "Send via WhatsApp" if the tab didn't open.`,
        action: { label: "Send via WhatsApp", onClick: () => window.open(link, "_blank", "noopener") },
        duration: 8000,
      });
    } else {
      toast.success("Order updated");
    }
    load();
  };
  const assignBoyToOrder = async (orderId, deliveryBoyId) => {
    await api.put(`/admin/orders/${orderId}/assign`, { delivery_boy_id: deliveryBoyId });
    toast.success("Delivery boy assigned");
    load();
  };
  const saveDeliveryBoy = async (e) => {
    e.preventDefault();
    if (boyForm.id) {
      await api.put(`/admin/delivery-boys/${boyForm.id}`, { name: boyForm.name, mobile: boyForm.mobile, vehicle: boyForm.vehicle, status: boyForm.status });
      toast.success("Delivery boy updated");
    } else {
      await api.post("/admin/delivery-boys", { name: boyForm.name, mobile: boyForm.mobile, vehicle: boyForm.vehicle, status: boyForm.status });
      toast.success("Delivery boy added");
    }
    setBoyForm({ id: "", name: "", mobile: "", vehicle: "", status: "active" });
    load();
  };
  const editDeliveryBoy = (boy) => setBoyForm({ id: boy.id, name: boy.name, mobile: boy.mobile, vehicle: boy.vehicle || "", status: boy.status || "active" });
  const deleteDeliveryBoy = async (id) => { await api.delete(`/admin/delivery-boys/${id}`); toast.success("Delivery boy removed"); load(); };
  const adjustStock = async (product, change_type) => { await api.post("/admin/inventory/adjust", { product_id: product.id, change_type, quantity: 5, note: "Quick admin adjustment" }); toast.success("Stock updated"); load(); };

  if (!isAdmin) return <section data-testid="admin-login-page" className="admin-login"><div className="admin-login-card"><h1 data-testid="admin-login-heading">BARNAWAL GENERAL STORE</h1><p data-testid="admin-login-subtitle">Blinkit-style Admin Dashboard</p><AuthPanel mode="admin" onDone={(u) => setUser(u)} /></div></section>;
  return (
    <section data-testid="admin-app" className="admin-shell">
      <aside data-testid="admin-sidebar" className="admin-sidebar"><div data-testid="admin-brand" className="admin-brand"><span>B</span><b>BARNAWAL</b><small>30 Minute Delivery</small></div>{menu.map(([key, label, Icon]) => <button data-testid={`admin-menu-${key}-button`} key={key} className={active === key ? "active" : ""} onClick={() => setActive(key)}><Icon size={18} />{label}</button>)}<button data-testid="admin-logout-button" onClick={() => { logout("admin"); setUser(null); }}><LogOut size={18} />Logout</button></aside>
      <main data-testid="admin-main" className="admin-main"><header data-testid="admin-topbar" className="admin-topbar"><div><h1 data-testid="admin-page-title">{menu.find((m) => m[0] === active)?.[1]}</h1><p data-testid="admin-store-contact">{storeContactsLine} · COD Only</p></div><div className="admin-topbar-right"><div data-testid="admin-search" className="admin-search"><Search size={17} /><input data-testid="admin-search-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search products" /></div><button data-testid="admin-notification-bell-button" className="notification-bell" onClick={() => setShowNotifications((s) => !s)} type="button"><Bell size={20} />{unreadCount > 0 && <span data-testid="notification-badge" className="notification-badge">{unreadCount}</span>}</button>{showNotifications && <NotificationsDropdown notifications={notifications} unreadCount={unreadCount} onClose={() => setShowNotifications(false)} markAllRead={markAllRead} openOrder={openOrderFromNotification} store={store} storeContactsLine={storeContactsLine} />}</div></header>
        {selectedOrder && <OrderDetailModal order={selectedOrder} onClose={() => setSelectedOrder(null)} updateOrder={updateOrder} />}
        {active === "dashboard" && <Dashboard dashboard={dashboard} />}
        {active === "products" && <Products products={products} categories={categories} form={productForm} setForm={setProductForm} addProduct={addProduct} deleteProduct={deleteProduct} />}
        {active === "price-items" && <PriceItems products={products} categories={categories} form={productForm} setForm={setProductForm} addProduct={addProduct} updateProduct={updateProduct} deleteProduct={deleteProduct} />}
        {active === "price-sync" && <PriceSync products={products} categories={categories} reload={load} />}
        {active === "categories" && <Categories categories={categories} />}
        {active === "inventory" && <Inventory inventory={inventory} adjustStock={adjustStock} />}
        {active === "orders" && <Orders orders={orders} updateOrder={updateOrder} openOrder={setSelectedOrder} />}
        {active === "customers" && <Customers customers={customers} />}
        {active === "delivery" && <Delivery orders={orders} deliveryBoys={deliveryBoys} boyForm={boyForm} setBoyForm={setBoyForm} saveDeliveryBoy={saveDeliveryBoy} editDeliveryBoy={editDeliveryBoy} deleteDeliveryBoy={deleteDeliveryBoy} assignBoyToOrder={assignBoyToOrder} smsLogs={smsLogs} updateOrder={updateOrder} />}
        {active === "reports" && <Reports reports={reports} />}
        {active === "settings" && <SettingsPanel />}
      </main>
      {/* hidden audio for notification sound */}
      <audio ref={audioRef} data-testid="notification-audio" preload="auto" src="data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU"></audio>
    </section>
  );
}

function NotificationsDropdown({ notifications, unreadCount, onClose, markAllRead, openOrder, store = {}, storeContactsLine = "" }) {
  return (
    <div data-testid="notifications-dropdown" className="notifications-dropdown">
      <div className="notifications-header">
        <strong data-testid="notifications-dropdown-title">Notifications ({unreadCount} new)</strong>
        <div className="notifications-actions">
          <button data-testid="mark-all-read-button" className="ghost-btn" onClick={markAllRead} type="button">Mark all read</button>
          <button data-testid="close-notifications-button" className="ghost-btn" onClick={onClose} type="button"><X size={14} /></button>
        </div>
      </div>
      <div className="notifications-list">
        {notifications.length === 0 && <p data-testid="no-notifications-text" className="muted-text">No notifications yet</p>}
        {notifications.map((n) => {
          const confirmationMsg = `Hi ${n.customer_name}, ${store.name || "BARNAWAL GENERAL STORE"} has received your order ${n.order_no} for ₹${n.total_amount}. We are confirming your order and will deliver in ${store.delivery_time || "30 minutes"}. Pay on delivery. — ${storeContactsLine}`;
          const waLink = buildWhatsAppLink(n.mobile, confirmationMsg);
          return (
            <div data-testid={`notification-item-wrapper-${n.id}`} key={n.id} className={`notification-item-wrapper ${n.is_read ? "read" : "unread"}`}>
              <button
                data-testid={`notification-item-${n.id}`}
                type="button"
                className="notification-item"
                onClick={() => openOrder(n)}
              >
                <strong data-testid={`notification-title-${n.id}`}>{n.title}</strong>
                <span data-testid={`notification-message-${n.id}`}>{n.message}</span>
                <small data-testid={`notification-time-${n.id}`}>{new Date(n.created_at).toLocaleString()}</small>
              </button>
              <a
                data-testid={`notification-whatsapp-${n.id}`}
                className="whatsapp-row-btn notification-wa"
                href={waLink}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                title="Send WhatsApp confirmation"
              >
                <MessageCircle size={14} />
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function OrderDetailModal({ order, onClose, updateOrder }) {
  const statuses = ["New Order", "Accepted", "Packed", "Out For Delivery", "Delivered", "Cancelled"];
  return (
    <div data-testid="order-detail-modal" className="order-modal-overlay" onClick={onClose}>
      <div data-testid="order-detail-content" className="order-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="order-modal-header">
          <h2 data-testid="order-modal-title">Order {order.order_no}</h2>
          <button data-testid="close-order-modal-button" className="ghost-btn" onClick={onClose} type="button"><X size={16} /></button>
        </div>
        <div className="order-modal-body">
          <div className="order-modal-section">
            <h3 data-testid="order-customer-title">Customer Details</h3>
            <p data-testid="order-customer-name"><b>Name:</b> {order.customer_name}</p>
            <p data-testid="order-customer-mobile"><b>Mobile:</b> {order.mobile}</p>
            {order.email && <p data-testid="order-customer-email"><b>Email:</b> {order.email}</p>}
          </div>
          <div className="order-modal-section">
            <h3 data-testid="order-address-title">Delivery Address</h3>
            <p data-testid="order-address-line"><b>{order.address?.house}</b>, {order.address?.area}</p>
            <p data-testid="order-address-city">{order.address?.city} - {order.address?.pincode}</p>
            {order.address?.landmark && <p data-testid="order-address-landmark"><b>Landmark:</b> {order.address.landmark}</p>}
          </div>
          <div className="order-modal-section">
            <h3 data-testid="order-items-title">Items ({order.items?.length || 0})</h3>
            {(order.items || []).map((it, idx) => (
              <p key={idx} data-testid={`order-item-row-${idx}`}>
                {it.product_name} ({it.variant}) × {it.quantity} = ₹{it.quantity * it.selling_price}
              </p>
            ))}
          </div>
          <div className="order-modal-section">
            <h3 data-testid="order-total-title">Bill</h3>
            <p data-testid="order-subtotal">Subtotal: ₹{order.subtotal}</p>
            <p data-testid="order-delivery">Delivery: ₹{order.delivery_fee}</p>
            <p data-testid="order-gst">GST: ₹{order.gst}</p>
            <p data-testid="order-grand-total"><b>Total: ₹{order.total_amount}</b> ({order.payment_method})</p>
          </div>
          <div className="order-modal-section">
            <h3 data-testid="order-delivery-boy-title">Delivery Partner</h3>
            {order.delivery_boy_name ? (
              <>
                <p data-testid="order-delivery-boy-name"><b>Name:</b> {order.delivery_boy_name}</p>
                <p data-testid="order-delivery-boy-mobile"><b>Mobile:</b> {order.delivery_boy_mobile}</p>
              </>
            ) : (
              <p data-testid="order-delivery-boy-unassigned" className="muted-text">Not assigned yet — assign from the Delivery tab.</p>
            )}
            <a
              data-testid="order-modal-whatsapp-button"
              className="primary-btn whatsapp-primary"
              href={buildWhatsAppLink(order.mobile, `Hi ${order.customer_name}, your BARNAWAL order ${order.order_no} (₹${order.total_amount}) is ${order.status}.${order.delivery_boy_name ? ` Delivery partner: ${order.delivery_boy_name} (${order.delivery_boy_mobile}).` : ""} Pay on delivery. Thanks!`)}
              target="_blank"
              rel="noreferrer"
              style={{ marginTop: "0.75rem", display: "inline-flex", alignItems: "center", gap: ".4rem" }}
            >
              <MessageCircle size={16} /> Send WhatsApp to Customer
            </a>
          </div>
          <div className="order-modal-section">
            <h3 data-testid="order-status-title">Order Status</h3>
            <select
              data-testid="order-status-select"
              value={order.status}
              onChange={(e) => { updateOrder(order.id, e.target.value, order.delivery_boy_id); onClose(); }}
            >
              {Array.from(new Set([order.status, ...statuses])).map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}

function Dashboard({ dashboard }) {
  if (!dashboard) return <div data-testid="admin-dashboard-loading" className="page-loader">Loading dashboard...</div>;
  const k = dashboard.kpis;
  const cards = [["Total Products", k.total_products], ["Total Categories", k.total_categories], ["Total Orders", k.total_orders], ["Pending Orders", k.pending_orders], ["Delivered Orders", k.delivered_orders], ["Total Customers", k.total_customers], ["Total Revenue", `₹${k.total_revenue}`], ["Low Stock Products", k.low_stock_products], ["Out of Stock Products", k.out_of_stock_products]];
  const lastSync = dashboard.last_price_sync;
  return <div data-testid="admin-dashboard" className="admin-stack">
    {lastSync && <div data-testid="last-price-sync-card" className="admin-panel last-sync-card">
      <div><h2 data-testid="last-price-sync-title">Last Price Sync</h2><p data-testid="last-price-sync-when"><b>{new Date(lastSync.created_at).toLocaleString()}</b> · source: {lastSync.source}</p></div>
      <div className="last-sync-stats">
        <span data-testid="last-sync-matched"><strong>{lastSync.matched_count}</strong> updated</span>
        <span data-testid="last-sync-unmatched"><strong>{lastSync.unmatched_count}</strong> unmatched</span>
        <span data-testid="last-sync-skipped"><strong>{lastSync.skipped_count}</strong> skipped</span>
      </div>
    </div>}
    <div className="kpi-grid">{cards.map(([label, value]) => <div data-testid={`kpi-card-${label.toLowerCase().replaceAll(" ", "-")}`} className="kpi-card" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>
    <div className="admin-two-col"><div className="admin-panel"><h2 data-testid="sales-chart-title">Sales Chart</h2><ResponsiveContainer width="100%" height={260}><BarChart data={dashboard.sales_chart}><CartesianGrid strokeDasharray="3 3" stroke="#303034" /><XAxis dataKey="name" stroke="#a1a1aa" /><YAxis stroke="#a1a1aa" /><Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46" }} /><Bar dataKey="revenue" fill="#22c55e" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div><div className="admin-panel"><h2 data-testid="recent-orders-title">Recent Orders</h2>{dashboard.recent_orders.map((o) => <p data-testid={`recent-order-${o.id}`} key={o.id}><b>{o.order_no}</b><span>{o.status}</span><strong>₹{o.total_amount}</strong></p>)}</div></div>
    <div className="admin-panel"><h2 data-testid="top-products-title">Top Selling Products</h2><div className="mini-grid">{dashboard.top_products.map((p) => <span data-testid={`top-product-${p.id}`} key={p.id}>{p.product_name}</span>)}</div></div>
  </div>;
}

function PriceSync({ products, categories, reload }) {
  const [report, setReport] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [filterCategory, setFilterCategory] = useState("");
  const [filterQ, setFilterQ] = useState("");
  const [edits, setEdits] = useState({});
  const [logs, setLogs] = useState([]);
  const [savingBulk, setSavingBulk] = useState(false);

  const loadLogs = async () => {
    const { data } = await api.get("/admin/price-sync/logs");
    setLogs(data.logs || []);
  };
  useEffect(() => { loadLogs(); }, []);

  const downloadTemplate = async () => {
    const res = await api.get("/admin/price-sync/template", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement("a");
    a.href = url; a.download = "barnawal-price-sync-template.csv"; a.click();
    window.URL.revokeObjectURL(url);
  };

  const uploadCsv = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData(); fd.append("file", file);
      const { data } = await api.post("/admin/price-sync/csv", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setReport(data.report);
      toast.success(`Synced: ${data.report.matched_count} updated · ${data.report.unmatched_count} unmatched · ${data.report.skipped_count} skipped`);
      reload();
      loadLogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const filtered = useMemo(() => {
    return products.filter((p) => (!filterCategory || p.category === filterCategory) && (!filterQ || (p.product_name || "").toLowerCase().includes(filterQ.toLowerCase())));
  }, [products, filterCategory, filterQ]);

  const setEdit = (id, key, value) => setEdits((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), [key]: value } }));

  const saveBulk = async () => {
    const items = Object.entries(edits)
      .map(([product_id, v]) => ({ product_id, mrp: parseFloat(v.mrp), selling_price: parseFloat(v.selling_price) }))
      .filter((it) => !Number.isNaN(it.mrp) && !Number.isNaN(it.selling_price));
    if (items.length === 0) { toast.info("No price edits to save"); return; }
    setSavingBulk(true);
    try {
      const { data } = await api.post("/admin/price-sync/bulk-edit", { items, source: "manual_bulk_edit" });
      setReport(data.report);
      toast.success(`Bulk saved: ${data.report.matched_count} updated, ${data.report.skipped_count} skipped`);
      setEdits({});
      reload();
      loadLogs();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Bulk save failed");
    } finally {
      setSavingBulk(false);
    }
  };

  return (
    <div data-testid="admin-price-sync" className="admin-stack">
      <div className="admin-panel">
        <h2 data-testid="price-sync-title">Price Sync · Update prices in bulk</h2>
        <p data-testid="price-sync-help" className="muted-text">
          Download the CSV template, fill MRP &amp; selling price from your source (Blinkit / Zepto / your own pricing), then upload. We only update <b>MRP, selling price, discount %, last updated</b> — no other product fields are touched.
        </p>
        <div className="admin-actions">
          <button data-testid="download-csv-template-button" className="primary-btn" type="button" onClick={downloadTemplate}>Download CSV Template</button>
          <label data-testid="upload-csv-label" className="ghost-btn" style={{ cursor: "pointer" }}>
            {uploading ? "Uploading..." : "Upload Filled CSV"}
            <input data-testid="upload-csv-input" type="file" accept=".csv" onChange={uploadCsv} style={{ display: "none" }} />
          </label>
        </div>
      </div>

      {report && (
        <div data-testid="price-sync-report" className="admin-panel">
          <h2 data-testid="price-sync-report-title">Last Upload Report</h2>
          <div className="last-sync-stats">
            <span data-testid="report-matched-count"><strong>{report.matched_count}</strong> updated</span>
            <span data-testid="report-unmatched-count"><strong>{report.unmatched_count}</strong> unmatched</span>
            <span data-testid="report-skipped-count"><strong>{report.skipped_count}</strong> skipped</span>
          </div>
          {report.unmatched.length > 0 && (
            <div className="report-section">
              <h3 data-testid="unmatched-products-title">Unmatched (manual review needed)</h3>
              <div className="admin-table-wrap"><table><thead><tr><th>Row</th><th>Product</th><th>Variant</th><th>Reason</th></tr></thead><tbody>
                {report.unmatched.map((u, i) => <tr data-testid={`unmatched-row-${i}`} key={i}><td>{u.row}</td><td>{u.product_name}</td><td>{u.variant}</td><td>{u.reason}</td></tr>)}
              </tbody></table></div>
            </div>
          )}
          {report.matched.length > 0 && (
            <div className="report-section">
              <h3 data-testid="matched-products-title">Updated</h3>
              <div className="admin-table-wrap"><table><thead><tr><th>Product</th><th>Variant</th><th>Old MRP → New</th><th>Old SP → New</th><th>Discount %</th></tr></thead><tbody>
                {report.matched.slice(0, 200).map((m, i) => <tr data-testid={`matched-row-${i}`} key={i}><td>{m.product_name}</td><td>{m.variant}</td><td>₹{m.old_mrp} → ₹{m.new_mrp}</td><td>₹{m.old_selling_price} → ₹{m.new_selling_price}</td><td>{m.discount_percent}%</td></tr>)}
              </tbody></table></div>
            </div>
          )}
        </div>
      )}

      <div className="admin-panel">
        <h2 data-testid="bulk-edit-title">Bulk Edit Prices</h2>
        <div className="admin-actions">
          <input data-testid="bulk-edit-search-input" placeholder="Search product" value={filterQ} onChange={(e) => setFilterQ(e.target.value)} />
          <select data-testid="bulk-edit-category-filter" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c.id} value={c.name}>{c.name}</option>)}
          </select>
          <button data-testid="bulk-edit-save-button" className="primary-btn" type="button" disabled={savingBulk || Object.keys(edits).length === 0} onClick={saveBulk}>
            {savingBulk ? "Saving..." : `Save ${Object.keys(edits).length} edits`}
          </button>
        </div>
        <div className="admin-table-wrap"><table data-testid="bulk-edit-table"><thead><tr><th>Product</th><th>Category</th><th>Variant</th><th>MRP</th><th>Selling Price</th><th>Discount %</th></tr></thead><tbody>
          {filtered.slice(0, 100).map((p) => {
            const e = edits[p.id] || {};
            const mrp = parseFloat(e.mrp ?? p.mrp);
            const sp = parseFloat(e.selling_price ?? p.selling_price);
            const disc = mrp > 0 ? Math.max(0, Math.round(((mrp - sp) / mrp) * 1000) / 10) : 0;
            return (
              <tr data-testid={`bulk-row-${p.id}`} key={p.id}>
                <td data-testid={`bulk-row-name-${p.id}`}>{p.product_name}</td>
                <td>{p.category}</td>
                <td>{p.variant}</td>
                <td><input data-testid={`bulk-row-mrp-${p.id}`} type="number" step="0.01" value={e.mrp ?? p.mrp} onChange={(ev) => setEdit(p.id, "mrp", ev.target.value)} /></td>
                <td><input data-testid={`bulk-row-selling-${p.id}`} type="number" step="0.01" value={e.selling_price ?? p.selling_price} onChange={(ev) => setEdit(p.id, "selling_price", ev.target.value)} /></td>
                <td data-testid={`bulk-row-discount-${p.id}`}>{disc}%</td>
              </tr>
            );
          })}
        </tbody></table></div>
        {filtered.length > 100 && <p className="muted-text">Showing first 100 of {filtered.length}. Narrow the search to edit more.</p>}
      </div>

      <div className="admin-panel">
        <h2 data-testid="sync-history-title">Sync History</h2>
        <div className="admin-table-wrap"><table><thead><tr><th>When</th><th>Source</th><th>Updated</th><th>Unmatched</th><th>Skipped</th><th>By</th></tr></thead><tbody>
          {logs.map((l) => <tr data-testid={`sync-log-row-${l.id}`} key={l.id}>
            <td>{new Date(l.created_at).toLocaleString()}</td><td>{l.source}</td><td>{l.matched_count}</td><td>{l.unmatched_count}</td><td>{l.skipped_count}</td><td>{l.performed_by}</td>
          </tr>)}
          {logs.length === 0 && <tr><td colSpan="6" className="muted-text">No sync runs yet</td></tr>}
        </tbody></table></div>
      </div>
    </div>
  );
}

function Products({ products, categories, form, setForm, addProduct, deleteProduct }) {
  const set = (k, v) => setForm({ ...form, [k]: v });
  const [uploading, setUploading] = useState(false);
  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) { toast.error("Please choose an image file"); return; }
    if (file.size > 5 * 1024 * 1024) { toast.error("Image must be under 5MB"); return; }
    const data = new FormData();
    data.append("file", file);
    setUploading(true);
    try {
      const { data: res } = await api.post("/admin/products/upload-image", data, { headers: { "Content-Type": "multipart/form-data" } });
      set("product_image", res.url);
      toast.success("Image uploaded");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Image upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };
  return <div data-testid="admin-products" className="admin-stack"><form data-testid="admin-add-product-form" className="admin-form" onSubmit={addProduct}>{["product_name", "hindi_name", "brand", "variant", "unit", "mrp", "selling_price", "stock_quantity"].map((key) => <input data-testid={`admin-product-${key}-input`} key={key} placeholder={key.replaceAll("_", " ")} value={form[key]} type={["mrp", "selling_price", "stock_quantity"].includes(key) ? "number" : "text"} onChange={(e) => set(key, e.target.value)} required={key === "product_name"} />)}<select data-testid="admin-product-category-select" value={form.category} onChange={(e) => set("category", e.target.value)}>{categories.map((c) => <option key={c.id}>{c.name}</option>)}</select><textarea data-testid="admin-product-description-input" placeholder="Description" value={form.description} onChange={(e) => set("description", e.target.value)} /><label data-testid="admin-product-image-upload-field" className="image-upload-field"><span>Product image (optional)</span><input data-testid="admin-product-image-file-input" type="file" accept="image/*" onChange={handleImageUpload} disabled={uploading} />{uploading && <small className="muted-text">Uploading...</small>}{form.product_image && <img data-testid="admin-product-image-preview" src={form.product_image} alt="preview" className="image-upload-preview" />}{form.product_image && <button data-testid="admin-product-image-clear-button" type="button" className="ghost-btn" onClick={() => set("product_image", "")}>Remove image</button>}</label><button data-testid="admin-add-product-submit-button" className="primary-btn">Add Product</button><button data-testid="admin-bulk-import-button" type="button" className="ghost-btn">Bulk Import Products</button></form><AdminTable title="Product Management" rows={products} columns={["product_image", "product_name", "category", "sku", "mrp", "selling_price", "stock_quantity", "status"]} action={(row) => <button data-testid={`admin-delete-product-${row.id}`} onClick={() => deleteProduct(row.id)}>Delete</button>} /></div>;
}

function PriceItems({ products, categories, form, setForm, addProduct, updateProduct, deleteProduct }) {
  const [edits, setEdits] = useState({});
  const set = (k, v) => setForm({ ...form, [k]: v });
  const setEdit = (id, key, value) => setEdits((prev) => ({ ...prev, [id]: { ...(prev[id] || {}), [key]: value } }));
  return <div data-testid="admin-price-items" className="admin-stack"><div data-testid="price-items-help-panel" className="admin-panel"><h2 data-testid="price-items-title">Price & Item Update Folder</h2><p data-testid="price-items-help-text"><span>Update price, stock, status, add items, or delete items here.</span><strong>Changes reflect in customer app</strong></p></div><form data-testid="price-items-add-product-form" className="admin-form" onSubmit={addProduct}>{["product_name", "hindi_name", "brand", "variant", "unit", "mrp", "selling_price", "stock_quantity"].map((key) => <input data-testid={`price-items-add-${key}-input`} key={key} placeholder={key.replaceAll("_", " ")} value={form[key]} type={["mrp", "selling_price", "stock_quantity"].includes(key) ? "number" : "text"} onChange={(e) => set(key, e.target.value)} required={key === "product_name"} />)}<select data-testid="price-items-add-category-select" value={form.category} onChange={(e) => set("category", e.target.value)}>{categories.map((c) => <option key={c.id}>{c.name}</option>)}</select><textarea data-testid="price-items-add-description-input" placeholder="Description" value={form.description} onChange={(e) => set("description", e.target.value)} /><button data-testid="price-items-add-product-submit-button" className="primary-btn">Add New Item</button></form><div data-testid="price-items-grid" className="price-update-grid">{products.map((product) => { const edit = edits[product.id] || {}; return <article data-testid={`price-item-card-${product.id}`} className="price-edit-card" key={product.id}><div><strong data-testid={`price-item-name-${product.id}`}>{product.product_name}</strong><small data-testid={`price-item-category-${product.id}`}>{product.category} · {product.sku}</small></div><label data-testid={`price-item-mrp-label-${product.id}`}>MRP<input data-testid={`price-item-mrp-input-${product.id}`} type="number" value={edit.mrp ?? product.mrp} onChange={(e) => setEdit(product.id, "mrp", e.target.value)} /></label><label data-testid={`price-item-selling-label-${product.id}`}>Selling Price<input data-testid={`price-item-selling-input-${product.id}`} type="number" value={edit.selling_price ?? product.selling_price} onChange={(e) => setEdit(product.id, "selling_price", e.target.value)} /></label><label data-testid={`price-item-stock-label-${product.id}`}>Stock<input data-testid={`price-item-stock-input-${product.id}`} type="number" value={edit.stock_quantity ?? product.stock_quantity} onChange={(e) => setEdit(product.id, "stock_quantity", e.target.value)} /></label><label data-testid={`price-item-status-label-${product.id}`}>Status<select data-testid={`price-item-status-select-${product.id}`} value={edit.status ?? product.status ?? "active"} onChange={(e) => setEdit(product.id, "status", e.target.value)}><option value="active">Active</option><option value="out_of_stock">Out of Stock</option><option value="inactive">Inactive</option></select></label><div className="row-actions"><button data-testid={`price-item-update-button-${product.id}`} className="primary-btn" onClick={() => updateProduct(product, edit)}>Update</button><button data-testid={`price-item-delete-button-${product.id}`} className="ghost-btn" onClick={() => deleteProduct(product.id)}>Delete</button></div></article>; })}</div></div>;
}

function Categories({ categories }) {
  const fallbackImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='360' height='240' viewBox='0 0 360 240'%3E%3Crect width='360' height='240' fill='%2318181b'/%3E%3Cpath d='M55 170h250l-74-82-47 54-35-40z' fill='%2322c55e' fill-opacity='.8'/%3E%3Ccircle cx='108' cy='84' r='28' fill='%2386efac'/%3E%3Ctext x='180' y='214' text-anchor='middle' fill='%23fafafa' font-family='Arial' font-size='18' font-weight='700'%3EBGS%3C/text%3E%3C/svg%3E";
  return <div data-testid="admin-categories" className="admin-stack"><div className="admin-actions"><button data-testid="admin-add-category-button" className="primary-btn">Add Category</button><button data-testid="admin-edit-category-button" className="ghost-btn">Edit Category</button><button data-testid="admin-delete-category-button" className="ghost-btn">Delete Category</button></div><div className="category-admin-grid">{categories.map((cat) => <article data-testid={`admin-category-${cat.id}`} key={cat.id}><img data-testid={`admin-category-image-${cat.id}`} src={cat.image || fallbackImage} onError={(e) => { e.currentTarget.src = fallbackImage; }} alt={cat.name} /><h3 data-testid={`admin-category-name-${cat.id}`}>{cat.name}</h3><p data-testid={`admin-category-count-${cat.id}`}>{cat.product_count} products</p></article>)}</div></div>;
}

function Inventory({ inventory, adjustStock }) {
  return <div data-testid="admin-inventory" className="admin-stack"><AdminTable title="Stock Management" rows={inventory.products} columns={["product_name", "stock_quantity", "minimum_stock", "status"]} action={(row) => <div className="row-actions"><button data-testid={`stock-in-${row.id}`} onClick={() => adjustStock(row, "stock_in")}>Stock In</button><button data-testid={`stock-out-${row.id}`} onClick={() => adjustStock(row, "stock_out")}>Stock Out</button></div>} /><div className="admin-panel"><h2 data-testid="inventory-history-title">Inventory History</h2>{inventory.logs.slice(0, 12).map((log) => <p data-testid={`inventory-log-${log.id}`} key={log.id}><b>{log.change_type}</b> {log.quantity} · {log.note}</p>)}</div></div>;
}

function Orders({ orders, updateOrder, openOrder }) {
  const statuses = ["Accepted", "Packed", "Out For Delivery", "Delivered", "Cancelled"];
  return <div data-testid="admin-orders" className="admin-stack"><AdminTable title="Order Management" rows={orders} columns={["order_no", "customer_name", "mobile", "email", "delivery_boy_name", "total_amount", "payment_method", "status"]} action={(row) => <div className="row-actions"><button data-testid={`admin-view-order-${row.id}`} className="ghost-btn" type="button" onClick={() => openOrder(row)}>View</button><select data-testid={`admin-order-status-${row.id}`} value={row.status} onChange={(e) => updateOrder(row.id, e.target.value, row.delivery_boy_id)}>{Array.from(new Set([row.status, ...statuses])).map((s) => <option key={s}>{s}</option>)}</select></div>} /></div>;
}

function Customers({ customers }) {
  return <div data-testid="admin-customers" className="admin-stack"><AdminTable title="Customer Management" rows={customers} columns={["full_name", "mobile", "total_orders", "total_spent", "last_order_date"]} /></div>;
}

function Delivery({ orders, deliveryBoys, boyForm, setBoyForm, saveDeliveryBoy, editDeliveryBoy, deleteDeliveryBoy, assignBoyToOrder, smsLogs, updateOrder }) {
  const assigned = useMemo(() => orders.filter((o) => ["Packed", "Out For Delivery", "Delivered", "Accepted", "New Order"].includes(o.status)), [orders]);
  const activeBoys = deliveryBoys.filter((b) => b.status === "active");
  const set = (k, v) => setBoyForm({ ...boyForm, [k]: v });
  return (
    <div data-testid="admin-delivery" className="admin-stack">
      <div className="delivery-panel">
        <h2 data-testid="delivery-management-title">Delivery Management</h2>
        <strong data-testid="admin-delivery-time">Delivery Time: 30 Minutes</strong>
        <p data-testid="assigned-orders-count">Active Orders: {assigned.length} · Delivery Boys: {deliveryBoys.length}</p>
      </div>

      <div className="admin-panel">
        <h2 data-testid="delivery-boys-section-title">Delivery Boys</h2>
        <form data-testid="delivery-boy-form" className="admin-form" onSubmit={saveDeliveryBoy}>
          <input data-testid="delivery-boy-name-input" placeholder="Name *" value={boyForm.name} onChange={(e) => set("name", e.target.value)} required />
          <input data-testid="delivery-boy-mobile-input" placeholder="Mobile (10 digits) *" value={boyForm.mobile} onChange={(e) => set("mobile", e.target.value.replace(/\D/g, "").slice(0, 10))} required />
          <input data-testid="delivery-boy-vehicle-input" placeholder="Vehicle (e.g. UP65 AB 1234)" value={boyForm.vehicle} onChange={(e) => set("vehicle", e.target.value)} />
          <select data-testid="delivery-boy-status-select" value={boyForm.status} onChange={(e) => set("status", e.target.value)}>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button data-testid="delivery-boy-submit-button" className="primary-btn" type="submit">{boyForm.id ? "Update" : "Add"} Delivery Boy</button>
          {boyForm.id && <button data-testid="delivery-boy-cancel-edit-button" className="ghost-btn" type="button" onClick={() => setBoyForm({ id: "", name: "", mobile: "", vehicle: "", status: "active" })}>Cancel Edit</button>}
        </form>
        <div data-testid="delivery-boys-grid" className="price-update-grid">
          {deliveryBoys.map((boy) => (
            <article data-testid={`delivery-boy-card-${boy.id}`} className="price-edit-card" key={boy.id}>
              <div>
                <strong data-testid={`delivery-boy-name-${boy.id}`}>{boy.name}</strong>
                <small data-testid={`delivery-boy-mobile-${boy.id}`}>{boy.mobile} · {boy.vehicle || "No vehicle"}</small>
              </div>
              <span data-testid={`delivery-boy-status-${boy.id}`} className={`status-pill ${boy.status}`}>{boy.status}</span>
              <div className="row-actions">
                <button data-testid={`delivery-boy-edit-button-${boy.id}`} className="ghost-btn" type="button" onClick={() => editDeliveryBoy(boy)}>Edit</button>
                <button data-testid={`delivery-boy-delete-button-${boy.id}`} className="ghost-btn" type="button" onClick={() => deleteDeliveryBoy(boy.id)}>Delete</button>
              </div>
            </article>
          ))}
          {deliveryBoys.length === 0 && <p data-testid="no-delivery-boys-text" className="muted-text">No delivery boys added yet</p>}
        </div>
      </div>

      <div className="admin-panel">
        <h2 data-testid="active-orders-assignment-title">Active Orders · Assign Delivery</h2>
        <div data-testid="active-orders-list" className="admin-stack">
          {assigned.map((o) => (
            <div data-testid={`active-order-row-${o.id}`} key={o.id} className="active-order-row">
              <div>
                <strong data-testid={`active-order-no-${o.id}`}>{o.order_no}</strong>
                <small data-testid={`active-order-customer-${o.id}`}>{o.customer_name} · {o.mobile} · ₹{o.total_amount}</small>
                <small data-testid={`active-order-address-${o.id}`}>{o.address?.house}, {o.address?.area}, {o.address?.pincode}</small>
                {o.delivery_boy_name && <small data-testid={`active-order-boy-${o.id}`}>Assigned: <b>{o.delivery_boy_name}</b> ({o.delivery_boy_mobile})</small>}
              </div>
              <div className="row-actions">
                <select
                  data-testid={`assign-boy-select-${o.id}`}
                  value={o.delivery_boy_id || ""}
                  onChange={(e) => assignBoyToOrder(o.id, e.target.value)}
                >
                  <option value="" disabled>Assign delivery boy</option>
                  {activeBoys.map((b) => <option key={b.id} value={b.id}>{b.name} ({b.mobile})</option>)}
                </select>
                <select
                  data-testid={`active-order-status-${o.id}`}
                  value={o.status}
                  onChange={(e) => updateOrder(o.id, e.target.value, o.delivery_boy_id)}
                >
                  {["New Order", "Accepted", "Packed", "Out For Delivery", "Delivered", "Cancelled"].map((s) => <option key={s}>{s}</option>)}
                </select>
                <a
                  data-testid={`whatsapp-customer-${o.id}`}
                  className="whatsapp-row-btn"
                  href={buildWhatsAppLink(o.mobile, `Hi ${o.customer_name}, your BARNAWAL order ${o.order_no} (₹${o.total_amount}) is ${o.status}.${o.delivery_boy_name ? ` Delivery partner: ${o.delivery_boy_name} (${o.delivery_boy_mobile}).` : ""} Pay on delivery. Thanks!`)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <MessageCircle size={14} /> WhatsApp
                </a>
              </div>
            </div>
          ))}
          {assigned.length === 0 && <p data-testid="no-active-orders-text" className="muted-text">No active orders</p>}
        </div>
      </div>

      <div className="admin-panel">
        <h2 data-testid="sms-logs-title">SMS Logs <small>(MOCKED — printed to backend logs)</small></h2>
        <div data-testid="sms-logs-list" className="admin-stack">
          {smsLogs.slice(0, 30).map((log) => (
            <div data-testid={`sms-log-${log.id}`} className="sms-log-row" key={log.id}>
              <div className="sms-log-head">
                <div>
                  <strong data-testid={`sms-log-order-${log.id}`}>{log.order_no} → {log.to_mobile}</strong>
                  <small data-testid={`sms-log-status-${log.id}`}>{log.status} · {new Date(log.created_at).toLocaleString()}</small>
                </div>
                <a
                  data-testid={`sms-log-whatsapp-${log.id}`}
                  className="whatsapp-row-btn"
                  href={buildWhatsAppLink(log.to_mobile, log.message)}
                  target="_blank"
                  rel="noreferrer"
                >
                  <MessageCircle size={14} /> Send via WhatsApp
                </a>
              </div>
              <p data-testid={`sms-log-message-${log.id}`}>{log.message}</p>
            </div>
          ))}
          {smsLogs.length === 0 && <p data-testid="no-sms-logs-text" className="muted-text">No SMS logs yet</p>}
        </div>
      </div>
    </div>
  );
}

function Reports({ reports }) {
  if (!reports) return <div data-testid="admin-reports-loading" className="page-loader">Loading reports...</div>;
  return <div data-testid="admin-reports" className="admin-stack"><div className="kpi-grid"><div className="kpi-card"><span>Daily Sales</span><strong data-testid="daily-sales-report">₹{reports.daily_sales}</strong></div><div className="kpi-card"><span>Weekly Sales</span><strong data-testid="weekly-sales-report">₹{reports.weekly_sales}</strong></div><div className="kpi-card"><span>Monthly Sales</span><strong data-testid="monthly-sales-report">₹{reports.monthly_sales}</strong></div></div><div className="admin-actions"><button data-testid="export-pdf-button" className="primary-btn">Export PDF</button><button data-testid="export-excel-button" className="ghost-btn">Export Excel</button></div><AdminTable title="Product Analytics" rows={reports.product_performance} columns={["product_name", "category", "stock_quantity", "selling_price", "rating"]} /></div>;
}

function SettingsPanel() {
  const [form, setForm] = useState(() => {
    const s = readStore();
    return {
      name: s.name || "",
      primary_whatsapp: s.primary_whatsapp || "",
      secondary_whatsapp: s.secondary_whatsapp || "",
      contact_primary: (s.contacts || [])[0] || "",
      contact_secondary: (s.contacts || [])[1] || "",
      delivery_time: s.delivery_time || "30 Minutes",
    };
  });
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);
  useEffect(() => {
    fetchStore().then((s) => setForm({
      name: s.name || "",
      primary_whatsapp: s.primary_whatsapp || "",
      secondary_whatsapp: s.secondary_whatsapp || "",
      contact_primary: (s.contacts || [])[0] || "",
      contact_secondary: (s.contacts || [])[1] || "",
      delivery_time: s.delivery_time || "30 Minutes",
    }));
  }, []);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        primary_whatsapp: form.primary_whatsapp.trim(),
        secondary_whatsapp: form.secondary_whatsapp.trim(),
        contacts: [form.contact_primary.trim(), form.contact_secondary.trim()].filter(Boolean),
        delivery_time: form.delivery_time.trim(),
      };
      const { data } = await api.put("/admin/settings", payload);
      writeStoreSettings(data);
      setSavedAt(new Date().toLocaleTimeString());
      toast.success("Store settings updated");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to update settings");
    } finally {
      setSaving(false);
    }
  };
  const primaryLink = form.primary_whatsapp ? `https://wa.me/${form.primary_whatsapp.replace(/\D/g, "")}` : "";
  const secondaryLink = form.secondary_whatsapp ? `https://wa.me/${form.secondary_whatsapp.replace(/\D/g, "")}` : "";
  return (
    <div data-testid="admin-settings" className="settings-grid">
      <form onSubmit={save} className="admin-panel" data-testid="store-settings-form">
        <h2 data-testid="store-settings-title">Store & WhatsApp Settings</h2>
        <label className="settings-field">
          <span>Store name</span>
          <input data-testid="settings-store-name-input" value={form.name} onChange={set("name")} placeholder="BARNAWAL GENERAL STORE" />
        </label>
        <label className="settings-field">
          <span>Primary Admin WhatsApp <small className="muted-text">(orders are routed here)</small></span>
          <input data-testid="settings-primary-whatsapp-input" value={form.primary_whatsapp} onChange={set("primary_whatsapp")} placeholder="e.g. 918381869505 or 8381869505" />
        </label>
        <label className="settings-field">
          <span>Secondary Admin WhatsApp</span>
          <input data-testid="settings-secondary-whatsapp-input" value={form.secondary_whatsapp} onChange={set("secondary_whatsapp")} placeholder="e.g. 918858351010" />
        </label>
        <label className="settings-field">
          <span>Customer-facing contact #1</span>
          <input data-testid="settings-contact-primary-input" value={form.contact_primary} onChange={set("contact_primary")} placeholder="8381869505" />
        </label>
        <label className="settings-field">
          <span>Customer-facing contact #2</span>
          <input data-testid="settings-contact-secondary-input" value={form.contact_secondary} onChange={set("contact_secondary")} placeholder="8858351010" />
        </label>
        <label className="settings-field">
          <span>Delivery time</span>
          <input data-testid="settings-delivery-time-input" value={form.delivery_time} onChange={set("delivery_time")} placeholder="30 Minutes" />
        </label>
        <div className="admin-actions">
          <button data-testid="settings-save-button" className="primary-btn" disabled={saving} type="submit">{saving ? "Saving..." : "Save settings"}</button>
          {savedAt && <span data-testid="settings-saved-indicator" className="muted-text">Saved at {savedAt}</span>}
        </div>
        <div className="settings-preview" style={{ marginTop: "1rem" }}>
          <p data-testid="settings-primary-whatsapp-link" className="muted-text">Primary click-to-chat: {primaryLink || "—"}</p>
          <p data-testid="settings-secondary-whatsapp-link" className="muted-text">Secondary click-to-chat: {secondaryLink || "—"}</p>
        </div>
      </form>
      <div className="admin-panel">
        <h2 data-testid="payment-settings-title">Payment Settings</h2>
        <p data-testid="cod-enabled-setting">Cash On Delivery: Enabled</p>
        <p data-testid="upi-disabled-setting">UPI: Disabled</p>
        <p data-testid="cards-disabled-setting">Cards: Disabled</p>
        <p data-testid="wallet-disabled-setting">Wallets: Disabled</p>
        <p data-testid="netbanking-disabled-setting">Net Banking: Disabled</p>
      </div>
      <div className="admin-panel">
        <h2 data-testid="auth-settings-title">Authentication</h2>
        <p data-testid="jwt-auth-setting">JWT Authentication Active</p>
        <p data-testid="customer-login-setting">Customer Login & Signup Enabled</p>
      </div>
    </div>
  );
}

function AdminTable({ title, rows = [], columns = [], action }) {
  const renderCell = (row, c) => {
    if (c === "product_image" || (c.includes("image") && typeof row[c] === "string" && (row[c].startsWith("http") || row[c].startsWith("data:")))) {
      return row[c] ? <img src={row[c]} alt="" className="admin-table-thumb" /> : <span className="muted-text">—</span>;
    }
    return String(row[c] ?? "-").slice(0, 80);
  };
  return <div data-testid={`table-${title.toLowerCase().replaceAll(" ", "-")}`} className="admin-table-panel"><h2 data-testid={`table-title-${title.toLowerCase().replaceAll(" ", "-")}`}>{title}</h2><div className="admin-table-wrap"><table><thead><tr>{columns.map((c) => <th data-testid={`table-header-${c}`} key={c}>{c.replaceAll("_", " ")}</th>)}{action && <th data-testid="table-header-action">Action</th>}</tr></thead><tbody>{rows.map((row) => <tr data-testid={`table-row-${row.id || row.order_no || row.mobile}`} key={row.id || row.order_no || row.mobile}>{columns.map((c) => <td data-testid={`table-cell-${row.id || row.order_no || row.mobile}-${c}`} key={c}>{renderCell(row, c)}</td>)}{action && <td data-testid={`table-action-${row.id || row.order_no}`}>{action(row)}</td>}</tr>)}</tbody></table></div></div>;
}