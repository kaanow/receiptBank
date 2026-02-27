import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { accounts as accountsApi } from "../api";

export default function AccountNew() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [friendlyName, setFriendlyName] = useState("");
  const [type, setType] = useState("personal");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const acc = await accountsApi.create({ name, friendly_name: friendlyName, type });
      if (acc && acc.id != null) {
        navigate(`/accounts/${acc.id}`, { replace: true });
      } else {
        setError("Could not create account");
      }
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h1>Add account</h1>
      <p><Link to="/">Dashboard</Link></p>
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. 123 Main St" />
        </label>
        <label>
          Short name (for filenames)
          <input type="text" value={friendlyName} onChange={(e) => setFriendlyName(e.target.value)} required placeholder="e.g. 123-Main" />
        </label>
        <label>
          Type
          <select value={type} onChange={(e) => setType(e.target.value)}>
            <option value="rental">Rental</option>
            <option value="employment">Employment</option>
            <option value="personal">Personal</option>
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Create account</button>
      </form>
    </div>
  );
}
