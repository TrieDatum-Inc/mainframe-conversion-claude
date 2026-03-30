import { render, screen } from "@testing-library/react";
import StatusBadge from "@/components/ui/StatusBadge";

describe("StatusBadge", () => {
  it("renders the status text", () => {
    render(<StatusBadge status="Active" />);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("applies green styles for Active status", () => {
    const { container } = render(<StatusBadge status="Active" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-green-100");
    expect(badge.className).toContain("text-green-800");
  });

  it("applies red styles for Inactive status", () => {
    const { container } = render(<StatusBadge status="Inactive" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-red-100");
  });

  it("applies yellow styles for Pending status", () => {
    const { container } = render(<StatusBadge status="Pending" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-yellow-100");
  });

  it("applies gray styles for unknown status", () => {
    const { container } = render(<StatusBadge status="Unknown" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("bg-gray-100");
  });

  it("renders dot variant", () => {
    const { container } = render(<StatusBadge status="Y" variant="dot" />);
    const dot = container.querySelector(".rounded-full");
    expect(dot).not.toBeNull();
    expect(dot?.className).toContain("bg-green-500");
  });
});
