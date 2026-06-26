import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import AuthPanel from "@/components/AuthPanel";
import DeliveryBadge from "@/components/DeliveryBadge";
import { api, getUser } from "@/lib/api";

export default function OrdersPage() {
  const [user, setUser] = useState(getUser());
  const [orders, setOrders] = useState([]);
  useEffect(() => { if (user) api.get("/orders").then(({ data }) => setOrders(data)); }, [user]);
  if (!user) return <AppShell><section data-testid="orders-login-required" className="checkout-auth"><AuthPanel onDone={(u) => setUser(u)} /></section></AppShell>;
  return <AppShell><section data-testid="orders-page" className="content-band"><DeliveryBadge /><h1 data-testid="orders-title">Order History</h1>{orders.length === 0 && <p data-testid="empty-orders-message" className="empty-state">No orders yet.</p>}{orders.map((order) => <article data-testid={`order-card-${order.id}`} key={order.id} className="order-card"><div><strong data-testid={`order-number-${order.id}`}>{order.order_no}</strong><p data-testid={`order-address-${order.id}`}>{order.address.house}, {order.address.area}</p></div><div><span data-testid={`order-status-${order.id}`} className="status-pill">{order.status}</span><b data-testid={`order-total-${order.id}`}>₹{order.total_amount}</b></div><div data-testid={`order-tracking-${order.id}`} className="tracking-line">{order.tracking.map((t) => t.status).join(" → ")}</div></article>)}</section></AppShell>;
}