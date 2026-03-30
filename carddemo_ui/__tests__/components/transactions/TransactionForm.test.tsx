import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TransactionForm from "@/components/transactions/TransactionForm";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

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

async function fillRequiredFields() {
  await userEvent.type(screen.getByLabelText(/Card Number/i), "4111111111111111");
  await userEvent.type(screen.getByLabelText(/Type Code/i), "SA");
  // Category Code and Amount already have default values (0)
  await userEvent.type(screen.getByLabelText(/Source/i), "WEB");
  await userEvent.type(screen.getByLabelText(/Description/i), "Test transaction");
  // Merchant ID already has default value (0)
  await userEvent.type(screen.getByLabelText(/Merchant Name/i), "Test Merchant");
  // Use the input ID directly since "City" label includes a required asterisk span
  await userEvent.type(document.getElementById("tran_merchant_city")!, "New York");
  await userEvent.type(document.getElementById("tran_merchant_zip")!, "10001");
}

describe("TransactionForm", () => {
  it("renders form fields", () => {
    render(<TransactionForm />);

    expect(screen.getByLabelText(/Card Number/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Type Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
    expect(screen.getByText("Preview")).toBeInTheDocument();
  });

  it("shows confirm dialog after preview", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({ message: "Preview ok" });

    render(<TransactionForm />);
    await fillRequiredFields();
    await userEvent.click(screen.getByText("Preview"));

    await waitFor(() => {
      expect(screen.getByText("Confirm Transaction")).toBeInTheDocument();
    });
  });

  it("calls API with confirm N for preview", async () => {
    (api.post as jest.Mock).mockResolvedValueOnce({ message: "Preview ok" });

    render(<TransactionForm />);
    await fillRequiredFields();
    await userEvent.click(screen.getByText("Preview"));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith(
        "/api/transactions",
        expect.objectContaining({ confirm: "N" }),
      );
    });
  });
});
