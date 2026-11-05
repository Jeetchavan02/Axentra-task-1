import { useState } from "react";

import { api, setToken } from "../api";
import ErrorBox from "../components/ErrorBox";
import ThemeToggle from "../components/ThemeToggle";

const EMPTY = { company_name: "", full_name: "", email: "", password: "" };

export default function AuthPage({ onLoggedIn }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [values, setValues] = useState(EMPTY);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const update = (event) => setValues({ ...values, [event.target.name]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const { email, password } = values;
    try {
      if (isRegistering) await api("/auth/register", { method: "POST", body: values });
      const { access_token } = await api("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      setToken(access_token);
      onLoggedIn();
    } catch (err) {
      setError(err);
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth-theme">
        <ThemeToggle />
      </div>
      <div className="card">
        <h1>{isRegistering ? "Register your company" : "Log in"}</h1>
        <p className="muted">Subscription Tracker</p>
        <ErrorBox error={error} />
        <form onSubmit={submit}>
          {isRegistering && (
            <>
              <label>
                Company name
                <input name="company_name" value={values.company_name} onChange={update} required />
              </label>
              <label>
                Your name
                <input name="full_name" value={values.full_name} onChange={update} required />
              </label>
            </>
          )}
          <label>
            Email
            <input name="email" type="email" autoComplete="email" value={values.email} onChange={update} required />
          </label>
          <label>
            Password{isRegistering && " (at least 8 characters)"}
            <input
              name="password"
              type="password"
              autoComplete={isRegistering ? "new-password" : "current-password"}
              value={values.password}
              onChange={update}
              required
            />
          </label>
          <button className="primary" disabled={busy}>
            {isRegistering ? "Create account" : "Log in"}
          </button>
        </form>
        <button
          className="link"
          onClick={() => {
            setIsRegistering(!isRegistering);
            setError(null);
          }}
        >
          {isRegistering ? "Already registered? Log in" : "New here? Register your company"}
        </button>
      </div>
    </div>
  );
}
