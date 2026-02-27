import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App.jsx";

describe("App", () => {
  it("renders ReceiptBank heading", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /receiptbank/i })).toBeInTheDocument();
  });
});
