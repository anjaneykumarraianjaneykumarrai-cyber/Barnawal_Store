import { Heart, Plus, Star } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { addToCart } from "@/lib/cart";
import { api } from "@/lib/api";

const fallbackImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='480' height='360' viewBox='0 0 480 360'%3E%3Crect width='480' height='360' fill='%2318181b'/%3E%3Crect x='40' y='48' width='400' height='264' rx='28' fill='%2327272a'/%3E%3Ccircle cx='150' cy='148' r='44' fill='%2322c55e' fill-opacity='.75'/%3E%3Cpath d='M110 255h260l-78-94-58 70-38-45z' fill='%2386efac' fill-opacity='.85'/%3E%3Ctext x='240' y='312' text-anchor='middle' fill='%23fafafa' font-family='Arial' font-size='22' font-weight='700'%3EBARNAWAL STORE%3C/text%3E%3C/svg%3E";

export default function ProductCard({ product, index = 0 }) {
  const save = async () => {
    try { await api.post(`/wishlist/${product.id}`); toast.success("Wishlist updated"); }
    catch { toast.info("Login to save wishlist"); }
  };
  const mrp = Number(product.mrp || 0);
  const sp = Number(product.selling_price || 0);
  const discount = mrp > 0 && sp > 0 && sp < mrp ? Math.round(((mrp - sp) / mrp) * 100) : 0;
  const showBestPrice = product.best_price === true || discount >= 20;
  return (
    <article data-testid={`product-card-${product.id}`} className="product-card" style={{ animationDelay: `${Math.min(index, 10) * 45}ms` }}>
      {showBestPrice && <span data-testid={`product-best-price-badge-${product.id}`} className="best-price-badge">Best Price</span>}
      {discount > 0 && <span data-testid={`product-discount-badge-${product.id}`} className="discount-badge">{discount}% OFF</span>}
      <button data-testid={`wishlist-button-${product.id}`} onClick={save} className="heart-btn" aria-label="Add to wishlist"><Heart size={16} /></button>
      <Link data-testid={`product-detail-link-${product.id}`} to={`/product/${product.id}`}>
        <div data-testid={`product-image-wrap-${product.id}`} className="product-image-wrap"><img data-testid={`product-image-${product.id}`} src={product.product_image || fallbackImage} onError={(e) => { e.currentTarget.src = fallbackImage; }} alt={product.product_name} /></div>
        <div className="product-meta"><span data-testid={`product-rating-${product.id}`}><Star size={12} fill="currentColor" /> {product.rating}</span><span data-testid={`product-stock-${product.id}`}>{product.stock_quantity > 0 ? `${product.stock_quantity} left` : "Out"}</span></div>
        <h3 data-testid={`product-name-${product.id}`}>{product.product_name}</h3>
        <p data-testid={`product-hindi-name-${product.id}`}>{product.hindi_name}</p>
      </Link>
      <div className="price-row">
        <div>
          <strong data-testid={`product-price-${product.id}`}>₹{sp}</strong>
          {mrp > sp && <del data-testid={`product-mrp-${product.id}`}>₹{mrp}</del>}
          {discount > 0 && <span data-testid={`product-discount-${product.id}`} className="discount-inline">{discount}% OFF</span>}
        </div>
        <button data-testid={`add-to-cart-button-${product.id}`} disabled={product.stock_quantity <= 0} onClick={() => { addToCart(product); toast.success("Added to cart"); }}><Plus size={16} />ADD</button>
      </div>
    </article>
  );
}
