import { Link, NavLink, useNavigate } from "react-router-dom";
import { Heart, Home, MessageCircle, Package, Search, ShoppingCart, User } from "lucide-react";
import { useEffect, useState } from "react";
import DeliveryBadge from "@/components/DeliveryBadge";
import { readCart, whatsappOrderLink } from "@/lib/cart";
import { fetchStore, readStore } from "@/lib/storeSettings";

export default function AppShell({ children, search, setSearch, onAuthClick }) {
  const [count, setCount] = useState(readCart().reduce((s, i) => s + i.quantity, 0));
  const [store, setStore] = useState(readStore());
  const navigate = useNavigate();
  useEffect(() => {
    const update = () => setCount(readCart().reduce((s, i) => s + i.quantity, 0));
    const updateStore = () => setStore(readStore());
    window.addEventListener("cart-updated", update);
    window.addEventListener("store-settings-updated", updateStore);
    fetchStore().then(updateStore);
    return () => {
      window.removeEventListener("cart-updated", update);
      window.removeEventListener("store-settings-updated", updateStore);
    };
  }, []);
  const contactsText = (store.contacts || []).join(" · ");
  return (
    <div data-testid="customer-app-shell" className="customer-shell">
      <header data-testid="customer-header" className="customer-header">
        <Link data-testid="store-logo-link" to="/" className="brand-mark"><span>B</span><div><strong data-testid="store-name-title">{store.name || "BARNAWAL GENERAL STORE"}</strong><small data-testid="store-contact-text">{contactsText}</small></div></Link>
        <div data-testid="home-search-container" className="search-box"><Search size={18} /><input data-testid="product-search-input" value={search || ""} onChange={(e) => setSearch?.(e.target.value)} placeholder="Search atta, tea, shampoo..." /></div>
        <DeliveryBadge compact />
        <a data-testid="header-whatsapp-order-button" className="whatsapp-btn" href={whatsappOrderLink(readCart())} target="_blank" rel="noreferrer"><MessageCircle size={18} /> WhatsApp Order</a>
        <button data-testid="profile-login-button" onClick={onAuthClick} className="icon-btn"><User size={18} /> Login</button>
        <button data-testid="header-cart-button" onClick={() => navigate("/cart")} className="cart-pill"><ShoppingCart size={18} /><span data-testid="header-cart-count">{count}</span></button>
      </header>
      <main data-testid="customer-main-content">{children}</main>
      <nav data-testid="mobile-bottom-navigation" className="bottom-nav">
        <NavLink data-testid="bottom-nav-home-link" to="/"><Home size={19} />Home</NavLink>
        <NavLink data-testid="bottom-nav-orders-link" to="/orders"><Package size={19} />Orders</NavLink>
        <NavLink data-testid="bottom-nav-cart-link" to="/cart"><ShoppingCart size={19} />Cart</NavLink>
        <NavLink data-testid="bottom-nav-profile-link" to="/profile"><Heart size={19} />Profile</NavLink>
      </nav>
      <a data-testid="floating-whatsapp-order-button" className="floating-whatsapp" href={whatsappOrderLink(readCart())} target="_blank" rel="noreferrer"><MessageCircle size={20} /><span>Order on WhatsApp</span></a>
    </div>
  );
}
