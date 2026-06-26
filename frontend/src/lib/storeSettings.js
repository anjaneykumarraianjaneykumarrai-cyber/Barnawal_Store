import { api } from "@/lib/api";

const KEY = "bgs_store_settings";

const DEFAULTS = {
  name: "BARNAWAL GENERAL STORE",
  contacts: ["8381869505", "8858351010"],
  primary_whatsapp: "918381869505",
  secondary_whatsapp: "918858351010",
  primary_whatsapp_link: "https://wa.me/918381869505",
  secondary_whatsapp_link: "https://wa.me/918858351010",
  delivery_time: "30 Minutes",
};

export function readStore() {
  try {
    const cached = JSON.parse(localStorage.getItem(KEY) || "null");
    return { ...DEFAULTS, ...(cached || {}) };
  } catch {
    return DEFAULTS;
  }
}

export function writeStore(data) {
  localStorage.setItem(KEY, JSON.stringify(data));
  window.dispatchEvent(new Event("store-settings-updated"));
}

export async function fetchStore() {
  try {
    const { data } = await api.get("/store");
    writeStore(data);
    return data;
  } catch {
    return readStore();
  }
}

export function primaryWhatsappLink(message = "") {
  const link = readStore().primary_whatsapp_link || DEFAULTS.primary_whatsapp_link;
  return message ? `${link}?text=${encodeURIComponent(message)}` : link;
}

export function contactsLine() {
  return (readStore().contacts || []).join(" · ");
}
