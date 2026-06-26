import { Bike, Clock } from "lucide-react";

export default function DeliveryBadge({ compact = false }) {
  return (
    <div data-testid="delivery-30-minutes-badge" className={`delivery-badge ${compact ? "compact" : ""}`}>
      <Bike size={compact ? 14 : 18} aria-hidden="true" />
      <span data-testid="delivery-30-minutes-text">Delivery in 30 Minutes</span>
      {!compact && <Clock size={16} aria-hidden="true" />}
    </div>
  );
}