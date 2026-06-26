import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, saveSession } from "@/lib/api";
import { fetchStore, readStore } from "@/lib/storeSettings";

export default function AuthPanel({ mode = "customer", onDone }) {
  const [tab, setTab] = useState("login");
  const [otp, setOtp] = useState("");
  const [form, setForm] = useState({ full_name: "", mobile: "", email: "", identifier: "", password: "", confirm_password: "" });
  const [store, setStore] = useState(readStore());
  useEffect(() => { fetchStore().then(setStore); }, []);
  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const requestOtp = async () => {
    try {
      const { data } = await api.post("/auth/request-otp", { identifier: form.identifier || form.mobile || form.email });
      setOtp(data.demo_otp);
      toast.success(`Demo OTP: ${data.demo_otp}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not send OTP. Please try again.");
    }
  };
  const submit = async (e) => {
    e.preventDefault();
    const url = mode === "admin" ? "/auth/admin-login" : tab === "signup" ? "/auth/signup" : "/auth/login";
    const payload = mode === "admin" ? { mobile: form.identifier, password: form.password } : tab === "signup" ? form : { identifier: form.identifier, password: form.password };
    try {
      const { data } = await api.post(url, payload);
      saveSession(data, mode === "admin" ? "admin" : "customer");
      toast.success(data.message);
      onDone?.(data.user);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      let msg = detail || "Something went wrong. Please try again.";
      if (status === 409) {
        msg = detail || "This mobile or email is already registered. Please log in instead.";
      } else if (status === 401) {
        msg = detail || "Invalid credentials. Please check your details.";
      } else if (status === 400) {
        msg = detail || "Please check the details and try again.";
      }
      toast.error(msg);
    }
  };

  return (
    <form data-testid={`${mode}-auth-form`} className="auth-panel" onSubmit={submit}>
      <div className="auth-tabs" data-testid={`${mode}-auth-tabs`}>
        {mode !== "admin" && <button data-testid="auth-login-tab-button" type="button" className={tab === "login" ? "active" : ""} onClick={() => setTab("login")}>Login</button>}
        {mode !== "admin" && <button data-testid="auth-signup-tab-button" type="button" className={tab === "signup" ? "active" : ""} onClick={() => setTab("signup")}>Signup</button>}
      </div>
      <h2 data-testid={`${mode}-auth-title`}>{mode === "admin" ? "Admin Login" : tab === "signup" ? "Create account" : "Customer Login"}</h2>
      {tab === "signup" && mode !== "admin" && <input data-testid="signup-full-name-input" placeholder="Full Name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} required />}
      {tab === "signup" && mode !== "admin" && <input data-testid="signup-mobile-input" placeholder="Mobile Number" value={form.mobile} onChange={(e) => update("mobile", e.target.value)} required />}
      {tab === "signup" && mode !== "admin" && <input data-testid="signup-email-input" placeholder="Email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} required />}
      {(tab === "login" || mode === "admin") && <input data-testid={`${mode}-login-identifier-input`} placeholder={mode === "admin" ? "Mobile Number" : "Mobile or Email"} value={form.identifier} onChange={(e) => update("identifier", e.target.value)} required />}
      <input data-testid={`${mode}-password-input`} placeholder="Password" type="password" value={form.password} onChange={(e) => update("password", e.target.value)} required />
      {tab === "signup" && mode !== "admin" && <input data-testid="signup-confirm-password-input" placeholder="Confirm Password" type="password" value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} required />}
      {mode !== "admin" && <button data-testid="request-demo-otp-button" className="ghost-btn" type="button" onClick={requestOtp}>Forgot password / Get OTP</button>}
      {otp && <div data-testid="demo-otp-visible-alert" className="otp-box">Demo OTP: <strong>{otp}</strong></div>}
      <button data-testid={`${mode}-auth-submit-button`} className="primary-btn" type="submit">{mode === "admin" ? "Login" : tab === "signup" ? "Signup" : "Login"}</button>
      {mode === "admin" && <p data-testid="admin-default-login-info" className="muted-text">Use {(store.contacts || []).join(" or ")} · admin123</p>}
    </form>
  );
}