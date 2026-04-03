/**
 * Screen footer — mirrors Row 24 PF key legend in COTRN screens.
 */
interface FooterAction {
  key: string;
  label: string;
  onClick?: () => void;
  href?: string;
}

interface ScreenFooterProps {
  actions: FooterAction[];
}

export default function ScreenFooter({ actions }: ScreenFooterProps) {
  return (
    <div className="border-t border-gray-700 bg-gray-950 px-4 py-2">
      <div className="flex gap-4 flex-wrap text-xs text-yellow-400 font-mono">
        {actions.map((action) => (
          <span key={action.key}>
            <span className="font-semibold">{action.key}</span>
            <span className="text-gray-400">={action.label}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
