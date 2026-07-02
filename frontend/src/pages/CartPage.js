import { Link } from "react-router-dom";
import { MessageCircle, Minus, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import DeliveryBadge from "@/components/DeliveryBadge";
import { cartTotal, readCart, updateQty, whatsappOrderLink } from "@/lib/cart";

const fallbackImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'%3E%3Crect width='160' height='160' fill='%2327272a'/%3E%3Ccircle cx='62' cy='58' r='24' fill='%2322c55e'/%3E%3Cpath d='M28 120h104L96 78 75 104 61 86z' fill='%2386efac'/%3E%3C/svg%3E";

const MIN_ORDER = 200;
const FREE_DELIVERY_ABOVE = 500;
const DELIVERY_FEE = 20;

export default function CartPage() {
  const [items, setItems] = useState(readCart());
  useEffect(() => { const sync = () => setItems(readCart()); window.addEventListener("cart-updated", sync); return () => window.removeEventListener("cart-updated", sync); }, []);
  const total = cartTotal(items);
  const meetsMin = total >= MIN_ORDER;
  const shortBy = Math.max(0, MIN_ORDER - total);
  const deliveryFee = total > FREE_DELIVERY_ABOVE ? 0 : DELIVERY_FEE;
  const shortForFreeDelivery = Math.max(0, FREE_DELIVERY_ABOVE + 1 - total);
  return (
    <AppShell>
      <section data-testid="cart-page" className="cart-layout">
        <div className="cart-main">
          <DeliveryBadge />
          <h1 data-testid="cart-title">Your Cart</h1>
          {items.length === 0 && <div data-testid="empty-cart-message" className="empty-state">Cart is empty. <Link data-testid="empty-cart-shop-link" to="/">Start shopping</Link></div>}
          {items.map((item) => (
            <div data-testid={`cart-item-${item.product_id}`} className="cart-item" key={item.product_id}>
              <img data-testid={`cart-item-image-${item.product_id}`} src={item.image || fallbackImage} onError={(e) => { e.currentTarget.src = fallbackImage; }} alt={item.product_name} />
              <div>
                <strong data-testid={`cart-item-name-${item.product_id}`}>{item.product_name}</strong>
                <p data-testid={`cart-item-variant-${item.product_id}`}>{item.variant}</p>
                <span data-testid={`cart-item-price-${item.product_id}`}>₹{item.selling_price}</span>
              </div>
              <div className="qty-control">
                <button data-testid={`cart-minus-button-${item.product_id}`} onClick={() => updateQty(item.product_id, item.quantity - 1)}><Minus size={14} /></button>
                <span data-testid={`cart-quantity-${item.product_id}`}>{item.quantity}</span>
                <button data-testid={`cart-plus-button-${item.product_id}`} onClick={() => updateQty(item.product_id, item.quantity + 1)}><Plus size={14} /></button>
                <button data-testid={`cart-remove-button-${item.product_id}`} onClick={() => updateQty(item.product_id, 0)}><Trash2 size={14} /></button>
              </div>
            </div>
          ))}
        </div>
        <aside data-testid="cart-summary" className="summary-box">
          <h2 data-testid="cart-summary-title">Bill Summary</h2>
          <p data-testid="cart-subtotal-row">Subtotal <b>₹{total}</b></p>
          <p data-testid="cart-delivery-row">Delivery Charge <b>{deliveryFee === 0 ? "FREE" : `₹${deliveryFee}`}</b></p>
          {meetsMin && deliveryFee > 0 && (
            <p data-testid="cart-free-delivery-hint" className="min-order-warning">
              Add <b>₹{shortForFreeDelivery}</b> more to get FREE delivery
            </p>
          )}
          <p data-testid="cart-payment-row">Payment Method <b>Cash on Delivery</b></p>
          <p data-testid="cart-payment-note">Pay when your order is delivered.</p>
          {!meetsMin && items.length > 0 && (
            <p data-testid="cart-min-order-warning" className="min-order-warning">
              Add <b>₹{shortBy}</b> more to qualify for home delivery (minimum order ₹{MIN_ORDER})
            </p>
          )}
          {meetsMin && (
            <p data-testid="cart-min-order-met" className="min-order-met">
              ✓ Home delivery available
            </p>
          )}
          <a data-testid="cart-whatsapp-order-button" className="whatsapp-wide" href={whatsappOrderLink(items)} target="_blank" rel="noreferrer">
            <MessageCircle size={18} /> Order Direct on WhatsApp
          </a>
          <Link
            data-testid="cart-checkout-link"
            className={`primary-btn ${(!items.length || !meetsMin) ? "disabled" : ""}`}
            to={(items.length && meetsMin) ? "/checkout" : "/cart"}
            onClick={(e) => { if (!items.length || !meetsMin) e.preventDefault(); }}
          >
            {!items.length ? "Cart is empty" : !meetsMin ? `Add ₹${shortBy} more` : "Checkout"}
          </Link>
        </aside>
      </section>
    </AppShell>
  );
}
