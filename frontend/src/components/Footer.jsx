/* Footer — static site footer shown on every page. */
export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div>
          <strong>ShopAI</strong> — your smart shopping destination.
        </div>
        <div>© {new Date().getFullYear()} ShopAI. For learning purposes.</div>
      </div>
    </footer>
  )
}
