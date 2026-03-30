import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DataTable, { type Column } from "@/components/ui/DataTable";

interface TestRow {
  id: number;
  name: string;
  status: string;
  [key: string]: unknown;
}

const columns: Column<TestRow>[] = [
  { key: "id", header: "ID" },
  { key: "name", header: "Name" },
  { key: "status", header: "Status", render: (val) => `[${val}]` },
];

const data: TestRow[] = [
  { id: 1, name: "Alice", status: "Active" },
  { id: 2, name: "Bob", status: "Inactive" },
];

describe("DataTable", () => {
  it("renders headers and rows", () => {
    render(<DataTable columns={columns} data={data} />);

    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("renders custom column renderer", () => {
    render(<DataTable columns={columns} data={data} />);

    expect(screen.getByText("[Active]")).toBeInTheDocument();
    expect(screen.getByText("[Inactive]")).toBeInTheDocument();
  });

  it("shows empty state when no data", () => {
    render(<DataTable columns={columns} data={[]} />);

    expect(screen.getByText("No records found.")).toBeInTheDocument();
  });

  it("calls onRowClick when a row is clicked", async () => {
    const onClick = jest.fn();
    render(<DataTable columns={columns} data={data} onRowClick={onClick} />);

    await userEvent.click(screen.getByText("Alice"));
    expect(onClick).toHaveBeenCalledWith(data[0]);
  });
});
