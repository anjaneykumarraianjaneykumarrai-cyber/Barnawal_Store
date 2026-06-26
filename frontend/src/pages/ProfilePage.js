import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import AuthPanel from "@/components/AuthPanel";
import { api, getUser, logout } from "@/lib/api";

export default function ProfilePage() {
  const [user, setUser] = useState(getUser());
  const [wishlist, setWishlist] = useState([]);
  const [notifications, setNotifications] = useState([]);
  useEffect(() => { if (user) { api.get("/wishlist").then(({ data }) => setWishlist(data)); api.get("/notifications").then(({ data }) => setNotifications(data)); } }, [user]);
  if (!user) return <AppShell><section data-testid="profile-login-required" className="checkout-auth"><AuthPanel onDone={(u) => setUser(u)} /></section></AppShell>;
  return <AppShell><section data-testid="profile-page" className="profile-grid"><div className="profile-card"><h1 data-testid="profile-title">My Profile</h1><p data-testid="profile-name">{user.full_name}</p><p data-testid="profile-mobile">{user.mobile}</p><p data-testid="profile-email">{user.email}</p><button data-testid="profile-logout-button" className="ghost-btn" onClick={() => { logout(); setUser(null); }}>Logout</button></div><div className="profile-card"><h2 data-testid="wishlist-title">Wishlist</h2>{wishlist.map((p) => <p data-testid={`wishlist-product-${p.id}`} key={p.id}>{p.product_name} · ₹{p.selling_price}</p>)}</div><div className="profile-card"><h2 data-testid="notifications-title">Notifications</h2>{notifications.map((n) => <p data-testid={`notification-${n.id}`} key={n.id}><b>{n.title}</b> {n.message}</p>)}</div></section></AppShell>;
}