import { readStore } from "@/lib/storeSettings";

export function readCart() {
  try {
    return JSON.parse(localStorage.getItem("bgs_cart") || "[]");
  } catch {
    return [];
  }
}

export function writeCart(items) {
  localStorage.setItem("bgs_cart", JSON.stringify(items));
  window.dispatchEvent(new Event("cart-updated"));
}

export function addToCart(product, quantity = 1) {
  const cart = readCart();
  const found = cart.find((item) => item.product_id === product.id);
  if (found) found.quantity += quantity;
  else cart.push({ product_id: product.id, product_name: product.product_name, variant: product.variant, quantity, selling_price: product.selling_price, image: product.product_image });
  writeCart(cart);
  return cart;
}

export function updateQty(productId, quantity) {
  const next = readCart().map((item) => item.product_id === productId ? { ...item, quantity } : item).filter((item) => item.quantity > 0);
  writeCart(next);
  return next;
}

export function clearCart() {
  writeCart([]);
}

export function cartTotal(items) {
  return items.reduce((sum, item) => sum + item.selling_price * item.quantity, 0);
}

export function whatsappOrderLink(items = []) {
  const store = readStore();
  const storeName = store.name || "BARNAWAL PROVISION STORE";
  const lines = [`Namaste ${storeName}, I want to order:`];
  if (items.length) {
    items.forEach((item, index) => lines.push(`${index + 1}. ${item.product_name} (${item.variant}) x ${item.quantity} = ₹${item.selling_price * item.quantity}`));
    lines.push(`Total: ₹${cartTotal(items)}`);
  } else {
    lines.push("Please help me place my grocery order.");
  }
  lines.push("Payment: Cash on Delivery");
  lines.push(`Delivery: ${store.delivery_time || "30 Minutes"}`);
  const number = store.primary_whatsapp || "918381869505";
  return `https://wa.me/${number}?text=${encodeURIComponent(lines.join("\n"))}`;
}