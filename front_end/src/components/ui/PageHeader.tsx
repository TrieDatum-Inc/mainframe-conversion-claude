/**
 * PageHeader component.
 *
 * Maps to the standard COUSR0x BMS map header (rows 1-2):
 *   Row 1: Tran: [TRNNAME]   [TITLE01]              Date: [CURDATE]
 *   Row 2: Prog: [PGMNAME]   [TITLE02]              Time: [CURTIME]
 *
 * Colors: TRNNAME/PGMNAME/CURDATE/CURTIME in BLUE, TITLE01/TITLE02 in YELLOW.
 */
interface PageHeaderProps {
  title: string;
  subtitle?: string;
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: '2-digit',
  });
  const timeStr = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

  return (
    <div className="bg-gray-900 text-sm font-mono px-4 py-3 rounded-t-lg">
      <div className="flex justify-between items-center">
        <div className="flex gap-6">
          <span className="text-blue-400">
            Tran: <span className="text-blue-300">CU00</span>
          </span>
          <span className="text-yellow-400 font-semibold">
            AWS Mainframe Modernization — CardDemo
          </span>
        </div>
        <span className="text-blue-400">
          Date: <span className="text-blue-300">{dateStr}</span>
        </span>
      </div>
      <div className="flex justify-between items-center mt-1">
        <div className="flex gap-6">
          <span className="text-blue-400">
            Prog: <span className="text-blue-300">COUSR</span>
          </span>
          <span className="text-yellow-300">{subtitle || 'User Administration'}</span>
        </div>
        <span className="text-blue-400">
          Time: <span className="text-blue-300">{timeStr}</span>
        </span>
      </div>
      <h1 className="text-white text-center mt-2 text-base font-bold">{title}</h1>
    </div>
  );
}
