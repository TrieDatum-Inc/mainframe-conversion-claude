import { render, screen, waitFor } from "@testing-library/react";
import CardTable from "@/components/cards/CardTable";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

// Mock api
jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
  },
}));

import { api } from "@/lib/api";

const mockResponse = {
  items: [
    { card_num: "4111111111111111", card_acct_id: 12345, card_active_status: "Y", card_expiration_date: "2025-12-31" },
    { card_num: "4222222222222222", card_acct_id: 12346, card_active_status: "N", card_expiration_date: "2024-06-30" },
  ],
  page: 1,
  page_size: 10,
  total_count: 2,
  has_next_page: false,
};

beforeEach(() => {
  (api.get as jest.Mock).mockReset();
});

describe("CardTable", () => {
  it("renders card list after loading", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);
    render(<CardTable />);

    await waitFor(() => {
      expect(screen.getByText("4111111111111111")).toBeInTheDocument();
    });
    expect(screen.getByText("4222222222222222")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("shows error on API failure", async () => {
    (api.get as jest.Mock).mockRejectedValueOnce(new Error("Network error"));
    render(<CardTable />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("calls API with correct page parameters", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);
    render(<CardTable />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/api/cards?page=1&page_size=10");
    });
  });
});
