/*
 * Temporary placeholder pages for routes that get their real implementation in
 * later sub-phases (6.2 auth, 6.3 catalog, 6.4 cart, 6.5 orders). Keeping them
 * as named stubs lets the full route table and navigation work from day one.
 */
function Stub({ title, phase }) {
  return (
    <div className="container page">
      <h1 className="section-title">{title}</h1>
      <p style={{ color: 'var(--color-text-muted)' }}>
        This page will be implemented in sub-phase {phase}.
      </p>
    </div>
  )
}

export const NotFoundPage = () => <Stub title="404 — Page not found" phase="—" />
