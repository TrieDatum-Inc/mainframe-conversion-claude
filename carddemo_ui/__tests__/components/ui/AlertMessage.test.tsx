import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AlertMessage from "@/components/ui/AlertMessage";

describe("AlertMessage", () => {
  it("renders the message text", () => {
    render(<AlertMessage type="info" message="Hello World" />);
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  it("applies success styling", () => {
    render(<AlertMessage type="success" message="Done" />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("bg-green-50");
  });

  it("applies error styling", () => {
    render(<AlertMessage type="error" message="Failed" />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("bg-red-50");
  });

  it("applies info styling", () => {
    render(<AlertMessage type="info" message="Note" />);
    const alert = screen.getByRole("alert");
    expect(alert.className).toContain("bg-blue-50");
  });

  it("renders dismiss button when onDismiss provided", () => {
    render(<AlertMessage type="info" message="Test" onDismiss={() => {}} />);
    expect(screen.getByLabelText("Dismiss")).toBeInTheDocument();
  });

  it("does not render dismiss button when no onDismiss", () => {
    render(<AlertMessage type="info" message="Test" />);
    expect(screen.queryByLabelText("Dismiss")).not.toBeInTheDocument();
  });

  it("calls onDismiss when dismiss clicked", async () => {
    const onDismiss = jest.fn();
    render(<AlertMessage type="error" message="Error" onDismiss={onDismiss} />);

    await userEvent.click(screen.getByLabelText("Dismiss"));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
