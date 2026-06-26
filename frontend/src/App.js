import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import CustomerApp from "@/pages/CustomerApp";
import ProductDetail from "@/pages/ProductDetail";
import CartPage from "@/pages/CartPage";
import CheckoutPage from "@/pages/CheckoutPage";
import OrdersPage from "@/pages/OrdersPage";
import ProfilePage from "@/pages/ProfilePage";
import AdminApp from "@/pages/AdminApp";

function App() {
  return (
    <div className="App dark" data-testid="app-root">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<CustomerApp />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin" element={<AdminApp />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </div>
  );
}

export default App;
