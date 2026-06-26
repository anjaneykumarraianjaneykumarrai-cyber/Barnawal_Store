import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import AppShell from "@/components/AppShell";
import DeliveryBadge from "@/components/DeliveryBadge";
import { api, getUser } from "@/lib/api";
import { cartTotal, clearCart, readCart } from "@/lib/cart";

export default function CheckoutPage() {
  const user = getUser();
  const [items] = useState(readCart());
  const [customer, setCustomer] = useState({
    name: user?.full_name || "",
    mobile: user?.mobile || "",
    email: user?.email || "",
  });
  const [address, setAddress] = useState({
    house: "",
    area: "",
    city: "Ghazipur",
    pincode: "",
    landmark: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const total = cartTotal(items);
  const MIN_ORDER = 200;
  const meetsMin = total >= MIN_ORDER;
  const shortBy = Math.max(0, MIN_ORDER - total);
  const delivery = 20;
  const gst = +(total * 0.05).toFixed(2);
  const grand = +(total + delivery + gst).toFixed(2);

  const updateCustomer = (k, v) => setCustomer((p) => ({ ...p, [k]: v }));
  const updateAddress = (k, v) => setAddress((p) => ({ ...p, [k]: v }));

  const placeOrder = async (e) => {
    e?.preventDefault?.();
    if (!items.length) {
      toast.error("Your cart is empty");
      return;
    }
    if (!meetsMin) {
      toast.error(`Minimum order ₹${MIN_ORDER} required for home delivery. Add ₹${shortBy} more.`);
      return;
    }
    if (!customer.name.trim()) return toast.error("Please enter your name");
    if (!/^\d{10}$/.test((customer.mobile || "").replace(/\D/g, "").slice(-10))) {
      return toast.error("Please enter a valid 10-digit mobile number");
    }
    if (!customer.email.trim() || !/.+@.+\..+/.test(customer.email)) {
      return toast.error("Please enter a valid email");
    }
    if (!address.house.trim() || !address.area.trim()) {
      return toast.error("Please enter house/flat and area");
    }
    if (!/^\d{6}$/.test(address.pincode)) {
      return toast.error("Please enter a valid 6-digit pincode");
    }
    if (!address.landmark.trim()) {
      return toast.error("Please enter a nearby landmark");
    }
    try {
      setSubmitting(true);
      const { data } = await api.post("/orders", {
        items,
        customer,
        address: { label: "Home", ...address },
      });
      clearCart();
      toast.success(`Order placed: ${data.order.order_no}`, {
        description: "Our store will contact you on WhatsApp / call shortly to confirm. Delivery in 30 minutes.",
        duration: 7000,
      });
      navigate("/orders");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to place order");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell>
      <section data-testid="checkout-page" className="checkout-layout">
        <form className="checkout-form" onSubmit={placeOrder}>
          <DeliveryBadge />
          <h1 data-testid="checkout-title">Checkout</h1>

          <div data-testid="customer-details-section" className="payment-box" style={{ marginBottom: 16 }}>
            <h2 data-testid="customer-details-title">Customer Details</h2>
            <div className="form-grid">
              <input
                data-testid="checkout-customer-name-input"
                placeholder="Full Name *"
                value={customer.name}
                onChange={(e) => updateCustomer("name", e.target.value)}
                required
              />
              <input
                data-testid="checkout-customer-mobile-input"
                placeholder="Mobile Number (10 digits) *"
                value={customer.mobile}
                onChange={(e) => updateCustomer("mobile", e.target.value.replace(/\D/g, "").slice(0, 10))}
                inputMode="numeric"
                required
              />
              <input
                data-testid="checkout-customer-email-input"
                placeholder="Email *"
                type="email"
                value={customer.email}
                onChange={(e) => updateCustomer("email", e.target.value)}
                required
              />
            </div>
          </div>

          <div data-testid="delivery-address-section" className="payment-box" style={{ marginBottom: 16 }}>
            <h2 data-testid="delivery-address-title">Delivery Address</h2>
            <div className="form-grid">
              <input
                data-testid="checkout-address-house-input"
                placeholder="House / Flat / Building No. *"
                value={address.house}
                onChange={(e) => updateAddress("house", e.target.value)}
                required
              />
              <input
                data-testid="checkout-address-area-input"
                placeholder="Area / Street / Colony *"
                value={address.area}
                onChange={(e) => updateAddress("area", e.target.value)}
                required
              />
              <input
                data-testid="checkout-address-city-input"
                placeholder="City *"
                value={address.city}
                onChange={(e) => updateAddress("city", e.target.value)}
                required
              />
              <input
                data-testid="checkout-address-pincode-input"
                placeholder="Pincode (6 digits) *"
                value={address.pincode}
                onChange={(e) => updateAddress("pincode", e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                required
              />
              <input
                data-testid="checkout-address-landmark-input"
                placeholder="Landmark *"
                value={address.landmark}
                onChange={(e) => updateAddress("landmark", e.target.value)}
                required
              />
            </div>
          </div>

          <div data-testid="checkout-payment-box" className="payment-box">
            <h2 data-testid="checkout-payment-title">Payment Method</h2>
            <strong data-testid="checkout-payment-method">Cash on Delivery Only</strong>
            <p data-testid="checkout-payment-note">Pay when your order is delivered.</p>
          </div>
        </form>

        <aside data-testid="checkout-summary" className="summary-box">
          <h2 data-testid="checkout-summary-title">Order Summary</h2>
          <p data-testid="checkout-items-count">{items.length} items</p>
          <p data-testid="checkout-subtotal-row">Subtotal <b>₹{total}</b></p>
          <p data-testid="checkout-delivery-row">Delivery Charge <b>₹{delivery}</b></p>
          <p data-testid="checkout-gst-row">GST <b>₹{gst}</b></p>
          <h3 data-testid="checkout-grand-total">Total ₹{grand}</h3>
          {!meetsMin && (
            <p data-testid="checkout-min-order-warning" className="min-order-warning">
              Minimum order ₹{MIN_ORDER} required. Add ₹{shortBy} more.
            </p>
          )}
          <button
            data-testid="place-order-cod-button"
            className="primary-btn"
            disabled={!items.length || submitting || !meetsMin}
            onClick={placeOrder}
            type="button"
          >
            {submitting ? "Placing..." : !meetsMin ? `Add ₹${shortBy} more` : "Place COD Order"}
          </button>
        </aside>
      </section>
    </AppShell>
  );
}
