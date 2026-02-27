import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { accounts as accountsApi, expenses as expensesApi } from "../api";

export default function UploadReceipt() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [category, setCategory] = useState("");
  const [file, setFile] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    accountsApi.list().then((accs) => {
      if (!accs.unauthorized) setAccounts(accs);
    });
  }, []);

  function onFileChange(e) {
    const f = e.target.files?.[0];
    setFile(f);
    setExtracted(null);
    if (f) {
      setLoading(true);
      setError("");
      expensesApi.extract(f).then(setExtracted).catch((err) => setError(err.message)).finally(() => setLoading(false));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file || !accountId) {
      setError("Select a file and an account");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const expense = await expensesApi.fromReceipt(file, Number(accountId), category || null);
      navigate(`/accounts/${expense.account_id}`, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Upload receipt</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Receipt (image or PDF)
          <input ref={fileInputRef} type="file" accept="image/*,application/pdf" onChange={onFileChange} />
        </label>
        {loading && !extracted && <p>Extracting data…</p>}
        {extracted && (
          <div className="extracted">
            <p>Vendor: {extracted.vendor}</p>
            <p>Amount: {extracted.amount != null ? `$${extracted.amount}` : "—"}</p>
            <p>Date: {extracted.date ? extracted.date.slice(0, 10) : "—"}</p>
            {extracted.tax_gst != null && <p>GST: ${extracted.tax_gst}</p>}
            {extracted.tax_pst != null && <p>PST: ${extracted.tax_pst}</p>}
          </div>
        )}
        <label>
          Account
          <select value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
            <option value="">Select account</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </label>
        <label>
          Category (optional)
          <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Utilities" />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading || !file || !accountId}>Save expense & receipt</button>
      </form>
    </div>
  );
}
