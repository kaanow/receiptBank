import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { accounts as accountsApi, reports as reportsApi } from "../api";

export default function Reports() {
  const [accounts, setAccounts] = useState([]);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [accountId, setAccountId] = useState("");
  const [taxesSeparate, setTaxesSeparate] = useState(false);
  const [includeReceipts, setIncludeReceipts] = useState(false);
  const [reportType, setReportType] = useState("monthly");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    accountsApi.list().then((accs) => {
      if (!accs.unauthorized) setAccounts(accs);
    });
  }, []);

  async function runReport(e) {
    e.preventDefault();
    if (!fromDate || !toDate) {
      setError("Set from and to dates");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const params = { from_date: fromDate, to_date: toDate, taxes_separate: taxesSeparate, include_receipts: includeReceipts };
      if (accountId) params.account_id = accountId;
      if (reportType === "tax") {
        const r = await reportsApi.tax(params);
        if (r?.unauthorized) setError("Not logged in");
        else if (typeof r?.blob === "function") {
          const blob = await r.blob();
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "receipts.zip";
          a.click();
          URL.revokeObjectURL(a.href);
        }
      } else {
        params.format = "csv";
        const r = await reportsApi.monthly(params);
        if (r?.unauthorized) setError("Not logged in");
        else if (typeof r?.blob === "function") {
          const blob = await r.blob();
          const a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = includeReceipts ? "monthly-receipts.zip" : "monthly-expenses.csv";
          a.click();
          URL.revokeObjectURL(a.href);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Reports</h1>
      <p><Link to="/">Back to dashboard</Link></p>
      <form onSubmit={runReport}>
        <label>
          Report type
          <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="monthly">Monthly expense</option>
            <option value="tax">Rental tax (by category)</option>
          </select>
        </label>
        <label>
          From date
          <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} required />
        </label>
        <label>
          To date
          <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} required />
        </label>
        <label>
          Account (optional)
          <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
            <option value="">All</option>
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </label>
        <label>
          <input type="checkbox" checked={taxesSeparate} onChange={(e) => setTaxesSeparate(e.target.checked)} />
          Show GST/PST separately
        </label>
        <label>
          <input type="checkbox" checked={includeReceipts} onChange={(e) => setIncludeReceipts(e.target.checked)} />
          Include receipt bundle (ZIP)
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {includeReceipts ? "Download report + receipts" : "Download report"}
        </button>
      </form>
    </div>
  );
}
