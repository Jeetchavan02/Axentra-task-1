import { useEffect, useState } from "react";

import { api } from "../api";
import ErrorBox from "../components/ErrorBox";

export default function ReportsPage() {
  const [spend, setSpend] = useState(null);
  const [renewals, setRenewals] = useState(null);
  const [days, setDays] = useState(30);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/reports/monthly-spend").then(setSpend).catch(setError);
  }, []);

  useEffect(() => {
    api("/reports/upcoming-renewals", { params: { days, limit: 100 } })
      .then(setRenewals)
      .catch(setError);
  }, [days]);

  return (
    <>
      <div className="toolbar">
        <h1>Reports</h1>
      </div>
      <ErrorBox error={error} />
      {!spend && !error && <p className="muted">Loading...</p>}

      {spend && (
        <>
          <div className="stats">
            <div className="stat">
              <span className="muted">Monthly spend</span>
              <b>{spend.total_monthly_spend}</b>
            </div>
            <div className="stat">
              <span className="muted">Active subscriptions</span>
              <b>{spend.active_subscriptions}</b>
            </div>
          </div>
          <section className="card">
            <h2>Monthly spend by vendor</h2>
            {spend.by_vendor.length === 0 ? (
              <p className="muted">No active subscriptions.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Vendor</th>
                      <th className="num">Per month</th>
                    </tr>
                  </thead>
                  <tbody>
                    {spend.by_vendor.map((vendor) => (
                      <tr key={vendor.vendor_id}>
                        <td>{vendor.vendor_name}</td>
                        <td className="num">{vendor.monthly_spend}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}

      <section className="card">
        <div className="toolbar">
          <h2 style={{ margin: "0 auto 0 0" }}>Upcoming renewals</h2>
          <select
            aria-label="Renewal window"
            value={days}
            onChange={(event) => setDays(Number(event.target.value))}
          >
            {[30, 60, 90, 365].map((option) => (
              <option key={option} value={option}>
                Next {option} days
              </option>
            ))}
          </select>
        </div>
        {!renewals && !error && <p className="muted">Loading...</p>}
        {renewals?.items.length === 0 && <p className="muted">Nothing renews in this period.</p>}
        {renewals?.items.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Vendor</th>
                  <th>Plan</th>
                  <th className="num">Price</th>
                  <th>Cycle</th>
                  <th>Renews</th>
                  <th className="num">Days left</th>
                </tr>
              </thead>
              <tbody>
                {renewals.items.map((item) => (
                  <tr key={item.subscription_id}>
                    <td>{item.vendor_name}</td>
                    <td>{item.plan_name}</td>
                    <td className="num">{item.price}</td>
                    <td>{item.billing_cycle}</td>
                    <td>{item.renewal_date}</td>
                    <td className="num">{item.days_until_renewal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
