import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { accounts as accountsApi, expenses as expensesApi } from "../api";
import { CRA_RENTAL_CATEGORIES } from "../craCategories";

function formatDateForInput(date) {
  if (!date) return "";
  const s = typeof date === "string" ? date : (date && date.slice ? date.slice(0, 10) : "");
  return s.slice(0, 10) || "";
}

function isImageFile(file) {
  return file && file.type && file.type.startsWith("image/");
}

export default function UploadReceipt() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [category, setCategory] = useState("");
  const [categoryOther, setCategoryOther] = useState("");
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [extracted, setExtracted] = useState(null);
  const [vendor, setVendor] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [taxGst, setTaxGst] = useState("");
  const [taxPst, setTaxPst] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const previewUrlRef = useRef(null);

  const selectedAccount = accounts.find((a) => String(a.id) === String(accountId));
  const isRental = selectedAccount?.type === "rental";

  useEffect(() => {
    accountsApi.list().then((accs) => {
      if (!accs.unauthorized) setAccounts(accs);
    });
  }, []);

  useEffect(() => {
    if (!file) {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
        previewUrlRef.current = null;
      }
      setPreviewUrl(null);
      return;
    }
    if (isImageFile(file)) {
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
      const url = URL.createObjectURL(file);
      previewUrlRef.current = url;
      setPreviewUrl(url);
      return () => {
        if (previewUrlRef.current) {
          URL.revokeObjectURL(previewUrlRef.current);
          previewUrlRef.current = null;
        }
      };
    }
    setPreviewUrl(null);
  }, [file]);

  useEffect(() => {
    if (!extracted) return;
    setVendor(extracted.vendor || "");
    setAmount(extracted.amount != null ? String(extracted.amount) : "");
    setDate(formatDateForInput(extracted.date));
    setTaxGst(extracted.tax_gst != null ? String(extracted.tax_gst) : "");
    setTaxPst(extracted.tax_pst != null ? String(extracted.tax_pst) : "");
  }, [extracted]);

  function onFileChange(e) {
    const f = e.target.files?.[0];
    setFile(f);
    setExtracted(null);
    setVendor("");
    setAmount("");
    setDate("");
    setTaxGst("");
    setTaxPst("");
    if (f) {
      setLoading(true);
      setError("");
      expensesApi.extract(f).then(setExtracted).catch((err) => setError(err.message)).finally(() => setLoading(false));
    }
  }

  function getCategoryValue() {
    if (isRental && category && category !== "Other") return category;
    if (isRental && category === "Other") return categoryOther.trim() || null;
    return category.trim() || null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file || !accountId) {
      setError("Select a file and an account");
      return;
    }
    const amountNum = amount.trim() ? parseFloat(amount) : null;
    if (amount.trim() && (isNaN(amountNum) || amountNum < 0)) {
      setError("Enter a valid amount");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const overrides = {};
      if (extracted) {
        overrides.vendor = vendor.trim() || extracted.vendor || "";
        overrides.date = date.trim() || formatDateForInput(extracted.date) || "";
        overrides.amount = amount.trim() ? parseFloat(amount) : (extracted.amount != null ? extracted.amount : undefined);
        overrides.tax_gst = taxGst.trim() !== "" ? parseFloat(taxGst) : (extracted.tax_gst != null ? extracted.tax_gst : null);
        overrides.tax_pst = taxPst.trim() !== "" ? parseFloat(taxPst) : 0;
      } else {
        if (vendor.trim()) overrides.vendor = vendor.trim();
        if (date.trim()) overrides.date = date.trim();
        if (amount.trim()) overrides.amount = amountNum;
        if (taxGst.trim()) overrides.tax_gst = parseFloat(taxGst);
        if (taxPst.trim()) overrides.tax_pst = parseFloat(taxPst);
      }
      const expense = await expensesApi.fromReceipt(file, Number(accountId), getCategoryValue(), overrides);
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
          <input ref={fileInputRef} type="file" accept="image/*,application/pdf,.heic" onChange={onFileChange} />
        </label>
        {file && (
          <div className="receipt-preview" aria-label="Receipt preview">
            {loading && !extracted ? (
              <p className="receipt-preview__status">Extracting data…</p>
            ) : extracted?.preview_data_url ? (
              <img src={extracted.preview_data_url} alt="Receipt" className="receipt-preview__img" />
            ) : extracted && previewUrl ? (
              <img src={previewUrl} alt="Receipt" className="receipt-preview__img" />
            ) : extracted ? (
              <p className="receipt-preview__pdf">PDF: {file.name}</p>
            ) : null}
          </div>
        )}
        {extracted && (
          <div className="extracted-fields">
            <p className="form-hint">Review and correct the extracted data before saving.</p>
            <label>
              Vendor
              <input type="text" value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="e.g. PETRO-CANADA" />
            </label>
            <label>
              Amount ($)
              <input type="number" step="0.01" min="0" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="Total including tax" />
            </label>
            <label>
              Date
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label>
              GST ($)
              <input type="number" step="0.01" min="0" value={taxGst} onChange={(e) => setTaxGst(e.target.value)} placeholder="Leave blank if none" />
            </label>
            <label>
              PST ($)
              <input type="number" step="0.01" min="0" value={taxPst} onChange={(e) => setTaxPst(e.target.value)} placeholder="Leave blank if none" />
            </label>
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
        {isRental ? (
          <>
            <label>
              Category (CRA rental)
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">— Select category —</option>
                {CRA_RENTAL_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
                <option value="Other">Other</option>
              </select>
            </label>
            {category === "Other" && (
              <label>
                Other category
                <input type="text" value={categoryOther} onChange={(e) => setCategoryOther(e.target.value)} placeholder="e.g. Landscaping" />
              </label>
            )}
          </>
        ) : (
          <label>
            Category (optional)
            <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Utilities" />
          </label>
        )}
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading || !file || !accountId}>Save expense & receipt</button>
      </form>
    </div>
  );
}
