import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BillPaymentForm from "@/components/billing/BillPaymentForm";

jest.mock("@/lib/api", () => ({
  api: {
    post: jest.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    field?: string;
    constructor(message: string, status: number, field?: string) {
      super(message);
      this.status = status;
      this.field = field;
    }
  },
}));

import { api } from "@/lib/api";

beforeEach(() => {
  (api.post as jest.Mock).mockReset();
});

describe("BillPaymentForm", () => {
  it("renders the account ID field and preview button", () => {
    render(<BillPaymentForm />);

    expect(screen.getByLabelText(/Account ID/i)).toBeInTheDocument();
    expect(screen.getByText("Preview Payment")).toBeInTheDocument();
  });

  it("shows confirm dialog after preview", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({
      message: "Payment preview for account 12345",
      previous_balance: 500.00,
    });

    render(<BillPaymentForm />);
    await userEvent.type(screen.getByLabelText(/Account ID/i), "12345");
    await userEvent.click(screen.getByText("Preview Payment"));

    await waitFor(() => {
      expect(screen.getByText("Confirm Bill Payment")).toBeInTheDocument();
    });
  });

  it("shows success result after confirming payment", async () => {
    (api.post as jest.Mock)
      .mockResolvedValueOnce({ message: "Preview", previous_balance: 500 })
      .mockResolvedValueOnce({
        message: "Payment successful",
        tran_id: "TXN999",
        previous_balance: 500,
        new_balance: 0,
      });

    render(<BillPaymentForm />);
    await userEvent.type(screen.getByLabelText(/Account ID/i), "12345");
    await userEvent.click(screen.getByText("Preview Payment"));

    await waitFor(() => {
      expect(screen.getByText("Pay Bill")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Pay Bill"));

    await waitFor(() => {
      expect(screen.getByText("Payment Successful")).toBeInTheDocument();
    });
  });

  it("shows error on API failure", async () => {
    (api.post as jest.Mock).mockRejectedValueOnce(new Error("Account not found"));

    render(<BillPaymentForm />);
    await userEvent.type(screen.getByLabelText(/Account ID/i), "99999");
    await userEvent.click(screen.getByText("Preview Payment"));

    await waitFor(() => {
      expect(screen.getByText("Account not found")).toBeInTheDocument();
    });
  });
});
