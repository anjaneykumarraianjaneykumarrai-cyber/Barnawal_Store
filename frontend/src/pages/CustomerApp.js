import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import AppShell from "@/components/AppShell";
import ProductCard from "@/components/ProductCard";
import DeliveryBadge from "@/components/DeliveryBadge";
import AuthPanel from "@/components/AuthPanel";
import { whatsappOrderLink } from "@/lib/cart";

const fallbackImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='360' height='240' viewBox='0 0 360 240'%3E%3Crect width='360' height='240' fill='%2318181b'/%3E%3Cpath d='M55 170h250l-74-82-47 54-35-40z' fill='%2322c55e' fill-opacity='.8'/%3E%3Ccircle cx='108' cy='84' r='28' fill='%2386efac'/%3E%3Ctext x='180' y='214' text-anchor='middle' fill='%23fafafa' font-family='Arial' font-size='18' font-weight='700'%3EBGS%3C/text%3E%3C/svg%3E";

export default function CustomerApp() {
  const [splash, setSplash] = useState(true);
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [active, setActive] = useState("");
  const [search, setSearch] = useState("");
  const [authOpen, setAuthOpen] = useState(false);

  useEffect(() => { setTimeout(() => setSplash(false), 900); api.get("/categories").then(({ data }) => setCategories(data)); }, []);
  useEffect(() => { api.get("/products", { params: { q: search, category: active, limit: 80 } }).then(({ data }) => setProducts(data.items)); }, [search, active]);
  const featured = useMemo(() => products.filter((p) => p.featured || p.best_seller).slice(0, 12), [products]);
  const openCategory = (categoryName) => {
    setSearch("");
    setActive(active === categoryName ? "" : categoryName);
    setTimeout(() => document.getElementById("products")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
  };

  if (splash) return <section data-testid="splash-screen" className="splash-screen"><div data-testid="splash-logo" className="splash-logo">BGS</div><h1 data-testid="splash-store-name">BARNAWAL GENERAL STORE</h1><DeliveryBadge /></section>;
  return (
    <AppShell search={search} setSearch={setSearch} onAuthClick={() => setAuthOpen(true)}>
      {authOpen && <div data-testid="auth-modal-backdrop" className="modal-backdrop"><div data-testid="auth-modal" className="modal"><button data-testid="auth-modal-close-button" className="modal-close" onClick={() => setAuthOpen(false)}><X size={18} /></button><AuthPanel onDone={() => setAuthOpen(false)} /></div></div>}
      <section data-testid="home-hero-section" className="hero-section">
        <div><DeliveryBadge /><h1 data-testid="home-main-heading">Daily grocery, personal care and home essentials.</h1><p data-testid="home-subtitle">COD only. Freshly packed from BARNAWAL GENERAL STORE.</p><div className="hero-actions"><button data-testid="hero-shop-now-button" onClick={() => document.getElementById("products")?.scrollIntoView({ behavior: "smooth" })}>Shop now</button><a data-testid="hero-whatsapp-order-button" href={whatsappOrderLink()} target="_blank" rel="noreferrer">Order Direct on WhatsApp</a></div></div>
      </section>
      <section data-testid="category-section" className="content-band"><div className="section-title"><h2 data-testid="category-section-title">Categories</h2><span data-testid="category-count-label">{categories.length} sections</span></div><div className="category-grid">{categories.map((cat) => <button data-testid={`category-button-${cat.id}`} key={cat.id} onClick={() => openCategory(cat.name)} className={active === cat.name ? "active" : ""}><img data-testid={`category-image-${cat.id}`} src={cat.image || fallbackImage} onError={(e) => { e.currentTarget.src = fallbackImage; }} alt={cat.name} /><strong data-testid={`category-name-${cat.id}`}>{cat.name}</strong><small data-testid={`category-product-count-${cat.id}`}>{cat.product_count} items</small></button>)}</div></section>
      <section data-testid="offers-section" className="offer-strip"><span data-testid="offer-coupon-code">BGS25</span><p data-testid="offer-copy">₹25 off on checkout · Cash on Delivery only · Pay when your order is delivered.</p></section>
      <section id="products" data-testid="products-section" className="content-band"><div className="section-title"><h2 data-testid="featured-products-title">{active || (search ? "Products" : "Featured Products")}</h2><span data-testid="products-count-label">{products.length} results</span></div>{!active && !search && <div className="product-grid featured-grid">{featured.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}</div>}<div data-testid="all-products-grid" className="product-grid">{products.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}</div></section>
    </AppShell>
  );
}