import { useCallback, useEffect, useState } from "react";

import { api } from "../api";
import { useOptions } from "../hooks";
import ErrorBox from "./ErrorBox";

export default function SeatsPanel({ subscriptionId, reloadKey, onClose }) {
  const url = `/subscriptions/${subscriptionId}/seats`;
  const [subscription, setSubscription] = useState(null);
  const employees = useOptions("/employees");
  const [seats, setSeats] = useState([]);
  const [employeeId, setEmployeeId] = useState("");
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const page = await api(url, { params: { limit: 100 } });
      setSeats(page.items);
    } catch (err) {
      setError(err);
    }
  }, [url]);

  useEffect(() => {
    setError(null);
    setEmployeeId("");
    load();
  }, [load]);

  // Re-read after edits on the list below, so the plan name and limit stay current.
  useEffect(() => {
    api(`/subscriptions/${subscriptionId}`)
      .then(setSubscription)
      .catch((err) => (err.status === 404 ? onClose() : setError(err)));
  }, [subscriptionId, reloadKey, onClose]);

  async function run(action) {
    setError(null);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err);
    }
  }

  const assign = (event) => {
    event.preventDefault();
    run(async () => {
      await api(url, { method: "POST", body: { employee_id: Number(employeeId) } });
      setEmployeeId("");
    });
  };

  const holders = new Set(seats.map((seat) => seat.employee_id));
  const available = employees.filter((employee) => !holders.has(employee.id));

  if (!subscription) return null;

  return (
    <section className="card" aria-label="Seats">
      <div className="toolbar">
        <h2 style={{ margin: "0 auto 0 0" }}>
          Seats on {subscription.plan_name}: {seats.length} of {subscription.seat_limit} used
        </h2>
        <button onClick={onClose}>Close</button>
      </div>
      <ErrorBox error={error} />
      <form className="toolbar" onSubmit={assign}>
        <select
          aria-label="Employee"
          value={employeeId}
          onChange={(event) => setEmployeeId(event.target.value)}
          required
        >
          <option value="">Choose an employee</option>
          {available.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.full_name} ({employee.email})
            </option>
          ))}
        </select>
        <button className="primary">Assign seat</button>
      </form>
      {seats.length === 0 ? (
        <p className="muted">No seats assigned.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Email</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {seats.map((seat) => (
                <tr key={seat.id}>
                  <td>{seat.employee_name}</td>
                  <td>{seat.employee_email}</td>
                  <td className="actions">
                    <button
                      className="danger"
                      onClick={() => run(() => api(`${url}/${seat.employee_id}`, { method: "DELETE" }))}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
