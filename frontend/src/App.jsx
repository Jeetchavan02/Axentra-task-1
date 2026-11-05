import { useEffect, useState } from "react";

import { api, clearToken, getToken, setSessionExpiredHandler } from "./api";
import ThemeToggle from "./components/ThemeToggle";
import AuthPage from "./pages/AuthPage";
import { PAGES } from "./pages";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(Boolean(getToken()));
  const [user, setUser] = useState(null);
  const [pageIndex, setPageIndex] = useState(0);

  const logOut = () => {
    clearToken();
    setUser(null);
    setLoggedIn(false);
  };

  useEffect(() => {
    setSessionExpiredHandler(logOut);
    if (loggedIn) api("/auth/me").then(setUser).catch(() => {});
  }, [loggedIn]);

  if (!loggedIn) return <AuthPage onLoggedIn={() => setLoggedIn(true)} />;

  const Page = PAGES[pageIndex]?.component;
  return (
    <div className="shell">
      <nav className="sidebar">
        <strong>Subscription Tracker</strong>
        {PAGES.map((page, index) => (
          <button
            key={page.label}
            className={index === pageIndex ? "active" : ""}
            onClick={() => setPageIndex(index)}
          >
            {page.label}
          </button>
        ))}
        <div className="account">
          <p className="email" title={user?.email}>
            {user?.email}
          </p>
          <ThemeToggle />
          <button onClick={logOut}>Log out</button>
        </div>
      </nav>
      <main>{Page && <Page />}</main>
    </div>
  );
}
