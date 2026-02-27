const API = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (res.status === 401) return { unauthorized: true };
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || JSON.stringify(err));
  }
  const contentType = res.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) return res.json();
  return res;
}

export const auth = {
  async me() {
    const r = await request("/auth/me");
    if (r.unauthorized) return null;
    return r;
  },
  async login(email, password) {
    const r = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    return r.user;
  },
  async logout() {
    await request("/auth/logout", { method: "POST" });
  },
  async register(email, password, display_name) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name: display_name || null }),
    });
  },
};

export const accounts = {
  list() {
    return request("/accounts");
  },
  create(data) {
    return request("/accounts", { method: "POST", body: JSON.stringify(data) });
  },
  get(id) {
    return request(`/accounts/${id}`);
  },
  update(id, data) {
    return request(`/accounts/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  },
  delete(id) {
    return request(`/accounts/${id}`, { method: "DELETE" });
  },
  share(id, email) {
    return request(`/accounts/${id}/share`, { method: "POST", body: JSON.stringify({ email }) });
  },
  revoke(accountId, userId) {
    return request(`/accounts/${accountId}/share/${userId}`, { method: "DELETE" });
  },
};

export const expenses = {
  list(accountId) {
    const q = accountId != null ? `?account_id=${accountId}` : "";
    return request(`/expenses${q}`);
  },
  create(data) {
    return request("/expenses", { method: "POST", body: JSON.stringify(data) });
  },
  get(id) {
    return request(`/expenses/${id}`);
  },
  update(id, data) {
    return request(`/expenses/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  },
  delete(id) {
    return request(`/expenses/${id}`, { method: "DELETE" });
  },
  async extract(file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/expenses/extract`, {
      method: "POST",
      credentials: "include",
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  },
  async fromReceipt(file, accountId, category) {
    const form = new FormData();
    form.append("file", file);
    form.append("account_id", String(accountId));
    if (category) form.append("category", category);
    const res = await fetch(`${API}/expenses/from-receipt`, {
      method: "POST",
      credentials: "include",
      body: form,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    return res.json();
  },
};

export const reports = {
  async tax(params) {
    const q = new URLSearchParams(params).toString();
    return request(`/reports/tax?${q}`);
  },
  async monthly(params) {
    const q = new URLSearchParams(params).toString();
    return request(`/reports/monthly?${q}`);
  },
};
