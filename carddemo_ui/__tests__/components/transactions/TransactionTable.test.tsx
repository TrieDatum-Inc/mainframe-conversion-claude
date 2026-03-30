import { render, screen, waitFor } from "@testing-library/react";
import TransactionTable from "@/components/transactions/TransactionTable";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
  },
}));

import { api } from "@/lib/api";

const mockResponse = {
  items: [
    { tran_id: "TXN001", tran_card_num: "4111111111111111", tran_type_cd: "SA", tran_amt: 150.75, tran_orig_ts: "2024-01-15T10:30:00" },
    { tran_id: "TXN002", tran_card_num: "4222222222222222", tran_type_cd: "CR", tran_amt: 25.0, tran_orig_ts: "2024-01-16T14:00:00" },
  ],
  page: 1,
  page_size: 10,
  total_count: 2,
  has_next_page: false,
};

beforeEach(() => {
  (api.get as jest.Mock).mockReset();
});

describe("TransactionTable", () => {
  it("renders transaction list after loading", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);
    render(<TransactionTable />);

    await waitFor(() => {
      expect(screen.getByText("TXN001")).toBeInTheDocument();
    });
    expect(screen.getByText("TXN002")).toBeInTheDocument();
    expect(screen.getByText("$150.75")).toBeInTheDocument();
  });

  it("shows error on failure", async () => {
    (api.get as jest.Mock).mockRejectedValueOnce(new Error("Server error"));
    render(<TransactionTable />);

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });
});
