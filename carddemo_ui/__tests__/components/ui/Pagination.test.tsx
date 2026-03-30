import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Pagination from "@/components/ui/Pagination";

describe("Pagination", () => {
  it("renders page info and navigation buttons", () => {
    render(
      <Pagination page={1} pageSize={10} totalCount={25} onPageChange={() => {}} />,
    );

    // Page 1 of 3 shown
    expect(screen.getByText("Previous")).toBeDisabled();
    expect(screen.getByText("Next")).toBeEnabled();
    expect(screen.getByText("25")).toBeInTheDocument(); // total count
  });

  it("disables Next button on last page", () => {
    render(
      <Pagination page={3} pageSize={10} totalCount={25} onPageChange={() => {}} />,
    );

    expect(screen.getByText("Next")).toBeDisabled();
    expect(screen.getByText("Previous")).toBeEnabled();
  });

  it("calls onPageChange when clicking Next", async () => {
    const onPageChange = jest.fn();
    render(
      <Pagination page={1} pageSize={10} totalCount={25} onPageChange={onPageChange} />,
    );

    await userEvent.click(screen.getByText("Next"));
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("calls onPageChange when clicking Previous", async () => {
    const onPageChange = jest.fn();
    render(
      <Pagination page={2} pageSize={10} totalCount={25} onPageChange={onPageChange} />,
    );

    await userEvent.click(screen.getByText("Previous"));
    expect(onPageChange).toHaveBeenCalledWith(1);
  });

  it("shows correct range for middle page", () => {
    render(
      <Pagination page={2} pageSize={10} totalCount={25} onPageChange={() => {}} />,
    );

    expect(screen.getByText("11")).toBeInTheDocument(); // range start
    expect(screen.getByText("20")).toBeInTheDocument(); // range end
    expect(screen.getByText("25")).toBeInTheDocument(); // total
  });

  it("renders the component without error when totalCount is 0", () => {
    const { container } = render(
      <Pagination page={1} pageSize={10} totalCount={0} onPageChange={() => {}} />,
    );

    expect(container.querySelector("nav")).toBeInTheDocument();
    expect(screen.getByText("Previous")).toBeDisabled();
    expect(screen.getByText("Next")).toBeDisabled();
  });
});
