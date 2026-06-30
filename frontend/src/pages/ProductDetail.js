import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import AppShell from "@/components/AppShell";
import DeliveryBadge from "@/components/DeliveryBadge";
import ProductCard from "@/components/ProductCard";
import { api } from "@/lib/api";
import { addToCart } from "@/lib/cart";

const fallbackImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='600' viewBox='0 0 600 600'%3E%3Crect width='600' height='600' fill='%2318181b'/%3E%3Crect x='70' y='80' width='460' height='380' rx='36' fill='%2327272a'/%3E%3Ccircle cx='210' cy='220' r='62' fill='%2322c55e'/%3E%3Cpath d='M130 390h340l-108-132-76 92-52-66z' fill='%2386efac'/%3E%3Ctext x='300' y='520' text-anchor='middle' fill='%23fafafa' font-family='Arial' font-size='28' font-weight='700'%3EBARNAWAL PROVISION STORE%3C/text%3E%3C/svg%3E";

export default function ProductDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  useEffect(() => { api.get(`/products/${id}`).then(({ data }) => setData(data)); }, [id]);
  if (!data) return <AppShell><div data-testid="product-detail-loading" className="page-loader">Loading product...</div></AppShell>;
  const { product, related, reviews } = data;
  return (
    <AppShell>
      <section data-testid="product-detail-page" className="detail-layout"><div data-testid="product-detail-image-card" className="detail-image"><img data-testid="product-detail-image" src={product.product_image || fallbackImage} onError={(e) => { e.currentTarget.src = fallbackImage; }} alt={product.product_name} /></div><div className="detail-info"><DeliveryBadge /><Link data-testid="product-back-home-link" to="/">← Back to store</Link><h1 data-testid="product-detail-name">{product.product_name}</h1><p data-testid="product-detail-hindi-name">{product.hindi_name}</p><p data-testid="product-detail-description">{product.description}</p><div className="detail-price"><strong data-testid="product-detail-price">₹{product.selling_price}</strong>{product.mrp > product.selling_price && <del data-testid="product-detail-mrp">₹{product.mrp}</del>}{product.mrp > 0 && product.selling_price < product.mrp && <span data-testid="product-detail-discount" className="discount-inline">{Math.round(((product.mrp - product.selling_price) / product.mrp) * 100)}% OFF</span>}{(product.best_price === true || (product.mrp > 0 && Math.round(((product.mrp - product.selling_price) / product.mrp) * 100) >= 20)) && <span data-testid="product-detail-best-price-badge" className="best-price-badge inline">Best Price</span>}<span data-testid="product-detail-stock">{product.stock_quantity > 0 ? "In Stock" : "Out of Stock"}</span></div><button data-testid="product-detail-add-cart-button" disabled={product.stock_quantity <= 0} onClick={() => { addToCart(product); toast.success("Added to cart"); }} className="primary-btn">Add to Cart</button></div></section>
      <section data-testid="product-reviews-section" className="content-band"><h2 data-testid="product-reviews-title">Reviews</h2>{reviews.length ? reviews.map((r) => <p data-testid={`review-${r.id}`} key={r.id}>⭐ {r.rating} · {r.comment}</p>) : <p data-testid="empty-reviews-message">No customer reviews yet.</p>}</section>
      <section data-testid="related-products-section" className="content-band"><h2 data-testid="related-products-title">Related products</h2><div className="product-grid">{related.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}</div></section>
    </AppShell>
  );
}