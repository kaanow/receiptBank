import { useState } from "react";
import { Link } from "react-router-dom";
import { expenses as expensesApi } from "../api";

export default function DebugOcr() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function onFileChange(e) {
    const f = e.target.files?.[0];
    setFile(f);
    setResult(null);
    setError("");
  }

  async function handleRun(e) {
    e.preventDefault();
    if (!file) {
      setError("Select a file");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await expensesApi.extractDebug(file);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Debug OCR</h1>
      <p className="form-hint">
        Run the same OCR + extract pipeline used for uploads. Use this to inspect raw text and parsed fields when troubleshooting.
      </p>
      <form onSubmit={handleRun}>
        <label>
          Receipt (image or PDF)
          <input type="file" accept="image/*,application/pdf,.heic" onChange={onFileChange} />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading || !file}>
          {loading ? "Running…" : "Run OCR & extract"}
        </button>
      </form>
      {result && (
        <div className="debug-ocr-result">
          <section>
            <h2>Raw OCR text</h2>
            <pre className="debug-ocr-raw">{result.raw_text || "(empty)"}</pre>
          </section>
          <section>
            <h2>Parsed fields</h2>
            <pre className="debug-ocr-parsed">{JSON.stringify(result.parsed ?? {}, null, 2)}</pre>
          </section>
        </div>
      )}
      <p><Link to="/">Back to dashboard</Link></p>
    </div>
  );
}
