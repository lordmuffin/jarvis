import { phases } from '@jarvis/shared/content';

export default function StatusTable() {
  return (
    <div className="overflow-x-auto">
      <table
        className="w-full font-mono text-sm border-collapse"
        role="table"
        aria-label="Jarvis phase status"
      >
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border)' }}>
            {['PHASE', 'GOAL', 'STATE', 'EFFORT'].map((h) => (
              <th
                key={h}
                className="text-left py-2 pr-6 text-xs uppercase tracking-widest"
                style={{ color: 'var(--fg-muted)' }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {phases.map((phase) => (
            <tr key={phase.id} style={{ borderBottom: '1px solid var(--border)' }}>
              <td className="py-2 pr-6 whitespace-nowrap text-fg">
                <span style={{ color: 'var(--accent)' }}>{phase.active ? '>' : ' '}</span>
                {phase.label}
              </td>
              <td
                className="py-2 pr-6"
                style={{ color: 'var(--fg-muted)', maxWidth: '400px' }}
              >
                {phase.goal}
              </td>
              <td
                className="py-2 pr-6 whitespace-nowrap"
                style={{
                  color:
                    phase.state === 'shipped'
                      ? 'var(--success)'
                      : phase.state === 'active'
                      ? 'var(--accent)'
                      : 'var(--warn)',
                }}
              >
                {phase.state}
              </td>
              <td className="py-2 whitespace-nowrap" style={{ color: 'var(--fg-subtle)' }}>
                {phase.effort}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
