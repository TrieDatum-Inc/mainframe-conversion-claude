import { render, screen, waitFor } from "@testing-library/react";
import UserTable from "@/components/users/UserTable";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock("@/lib/api", () => ({
  api: {
    get: jest.fn(),
    delete: jest.fn(),
  },
}));

import { api } from "@/lib/api";

const mockResponse = {
  items: [
    { usr_id: "admin1", usr_fname: "Alice", usr_lname: "Smith", usr_type: "A" },
    { usr_id: "user1", usr_fname: "Bob", usr_lname: "Jones", usr_type: "U" },
  ],
  page: 1,
  page_size: 10,
  total_count: 2,
  has_next_page: false,
};

beforeEach(() => {
  (api.get as jest.Mock).mockReset();
  (api.delete as jest.Mock).mockReset();
});

describe("UserTable", () => {
  it("renders user list after loading", async () => {
    (api.get as jest.Mock).mockResolvedValueOnce(mockResponse);
    render(<UserTable />);

    await waitFor(() => {
      expect(screen.getByText("admin1")).toBeInTheDocument();
    });
    expect(screen.getByText("user1")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("shows error on failure", async () => {
    (api.get as jest.Mock).mockRejectedValueOnce(new Error("Forbidden"));
    render(<UserTable />);

    await waitFor(() => {
      expect(screen.getByText("Forbidden")).toBeInTheDocument();
    });
  });
});
