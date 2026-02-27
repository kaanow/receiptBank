import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App.jsx";

vi.mock("./api", () => ({
  auth: { me: () => Promise.resolve(null), login: vi.fn(), logout: vi.fn(), register: vi.fn() },
  accounts: { list: vi.fn(() => Promise.resolve([])) },
  expenses: { list: vi.fn(() => Promise.resolve([])) },
  reports: { tax: vi.fn(), monthly: vi.fn() },
}));

describe("App", () => {
  it("renders ReceiptBank heading when not logged in", async () => {
    render(<App />);
    await screen.findByRole("heading", { name: /receiptbank/i }, { timeout: 2000 });
    expect(screen.getByRole("heading", { name: /receiptbank/i })).toBeInTheDocument();
  });
});
