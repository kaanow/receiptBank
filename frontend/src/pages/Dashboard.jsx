import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../useAuth";
import { accounts as accountsApi, expenses as expensesApi } from "../api";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([accountsApi.list(), expensesApi.list()])
      .then(([accs, exps]) => {
        setAccounts(accs.unauthorized ? [] : accs);
        setRecent(exps.unauthorized ? [] : exps.slice(0, 10));
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <header className="header">
        <h1>ReceiptBank</h1>
        <p>{user?.email}</p>
        <button type="button" onClick={logout}>Sign out</button>
      </header>
      <nav className="nav">
        <Link to="/upload">Upload receipt</Link>
        <Link to="/reports">Reports</Link>
        <Link to="/debug-ocr">Debug OCR</Link>
      </nav>
      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <section>
            <h2>Accounts</h2>
            {accounts.length === 0 ? (
              <p>No accounts yet. <Link to="/accounts/new">Add one</Link>.</p>
            ) : (
              <ul>
                {accounts.map((a) => (
                  <li key={a.id}>
                    <Link to={`/accounts/${a.id}`}>{a.name}</Link> ({a.type})
                  </li>
                ))}
              </ul>
            )}
            <p><Link to="/accounts/new">+ Add account</Link></p>
          </section>
          <section>
            <h2>Recent expenses</h2>
            {recent.length === 0 ? (
              <p>No expenses yet. Upload a receipt or add an expense.</p>
            ) : (
              <ul>
                {recent.map((e) => (
                  <li key={e.id}>
                    {e.date?.slice(0, 10)} {e.vendor} ${Number(e.amount).toFixed(2)}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
