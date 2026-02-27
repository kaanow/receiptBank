import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { accounts as accountsApi, expenses as expensesApi } from "../api";

export default function AccountDetail() {
  const { id } = useParams();
  const [account, setAccount] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([accountsApi.get(id), expensesApi.list(Number(id))]).then(([acc, exps]) => {
      setAccount(acc.unauthorized ? null : acc);
      setExpenses(exps.unauthorized ? [] : exps);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <p>Loading…</p>;
  if (!account) return <p>Account not found. <Link to="/">Dashboard</Link></p>;

  return (
    <div className="page">
      <h1>{account.name}</h1>
      <p><Link to="/">Dashboard</Link></p>
      <p><Link to="/upload">Upload receipt</Link></p>
      <h2>Expenses</h2>
      {expenses.length === 0 ? (
        <p>No expenses yet.</p>
      ) : (
        <ul>
          {expenses.map((e) => (
            <li key={e.id}>
              {e.date?.slice(0, 10)} {e.vendor} ${Number(e.amount).toFixed(2)} {e.category ? `(${e.category})` : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
