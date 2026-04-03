/**
 * PFKeyBar component — maps BMS row 24 PF key legend.
 *
 * COSGN00: "ENTER=Sign-on  F3=Exit"
 * COMEN01: "ENTER=Continue  F3=Exit"
 * COADM01: "ENTER=Continue  F3=Exit"
 *
 * BMS field: ASKIP,NORM, color=YELLOW (DFHYELLOW)
 */
interface PFKeyBarProps {
  keys: Array<{ key: string; label: string; onClick?: () => void }>;
}

export function PFKeyBar({ keys }: PFKeyBarProps) {
  return (
    <div className="bg-gray-900 text-yellow-400 font-mono text-sm px-4 py-1 border-t border-gray-700">
      {keys.map(({ key, label, onClick }, idx) => (
        <span key={key}>
          {idx > 0 && <span className="mx-2 text-gray-600">|</span>}
          {onClick ? (
            <button
              type="button"
              onClick={onClick}
              className="hover:text-yellow-200 focus:outline-none focus:underline"
              aria-label={`${key}: ${label}`}
            >
              <span className="text-white">{key}</span>={label}
            </button>
          ) : (
            <span>
              <span className="text-white">{key}</span>={label}
            </span>
          )}
        </span>
      ))}
    </div>
  );
}
