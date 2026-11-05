import { useCallback, useState } from "react";

import ResourcePage from "../components/ResourcePage";
import SeatsPanel from "../components/SeatsPanel";
import { useOptions } from "../hooks";

const CYCLES = [
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];
const STATUSES = [
  { value: "active", label: "Active" },
  { value: "cancelled", label: "Cancelled" },
];

export default function SubscriptionsPage() {
  const vendors = useOptions("/vendors");
  const [selectedId, setSelectedId] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);
  const closeSeats = useCallback(() => setSelectedId(null), []);
  const vendorOptions = vendors.map((vendor) => ({ value: vendor.id, label: vendor.name }));
  const vendorName = (id) => vendors.find((vendor) => vendor.id === id)?.name ?? `#${id}`;

  return (
    <>
      {selectedId && (
        <SeatsPanel subscriptionId={selectedId} reloadKey={reloadKey} onClose={closeSeats} />
      )}
    <ResourcePage
      title="Subscriptions"
      path="/subscriptions"
      defaults={{ billing_cycle: "monthly", status: "active" }}
      fields={[
        {
          name: "vendor_id",
          label: "Vendor",
          required: true,
          options: vendorOptions,
          placeholder: "Choose a vendor",
          emptyHint: "No vendors yet. Add one on the Vendors screen first.",
        },
        { name: "plan_name", label: "Plan", required: true },
        { name: "price", label: "Price per cycle", type: "number", min: 0, step: "0.01", required: true },
        { name: "billing_cycle", label: "Billing cycle", options: CYCLES },
        { name: "seat_limit", label: "Seat limit", type: "number", min: 1, required: true },
        { name: "renewal_date", label: "Renewal date", type: "date", required: true },
        { name: "status", label: "Status", options: STATUSES },
      ]}
      filters={[{ name: "status", label: "Status", options: STATUSES }]}
      columns={[
        { label: "Vendor", render: (row) => vendorName(row.vendor_id) },
        { label: "Plan", key: "plan_name" },
        { label: "Price", key: "price", numeric: true },
        { label: "Cycle", key: "billing_cycle" },
        { label: "Seat limit", key: "seat_limit", numeric: true },
        { label: "Renews", key: "renewal_date" },
        { label: "Status", key: "status" },
      ]}
      rowActions={(row) => <button onClick={() => setSelectedId(row.id)}>Seats</button>}
      onChanged={() => setReloadKey((key) => key + 1)}
      toBody={(values) => ({
        vendor_id: Number(values.vendor_id),
        plan_name: values.plan_name,
        price: String(values.price),
        billing_cycle: values.billing_cycle,
        seat_limit: Number(values.seat_limit),
        renewal_date: values.renewal_date,
        status: values.status,
      })}
    />
    </>
  );
}
