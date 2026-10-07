import { NavLink } from "react-router-dom";

const SOON_ITEMS = [
  { id: "tech", label: "TECH", icon: "◈" },
  { id: "sales", label: "SALES", icon: "◎" },
  { id: "mail", label: "MAIL", icon: "✉" },
  { id: "social", label: "SOCIAL", icon: "⌁" },
  { id: "journal", label: "JOURNAL", icon: "☰" },
] as const;

export function SidebarNav() {
  return (
    <nav className="sidebar" aria-label="Navigation principale">
      <div className="sidebar__brand" aria-hidden="true">
        DEVCOM
      </div>
      <NavLink to="/" end className="sidebar__link">
        <span className="sidebar__icon" aria-hidden="true">
          ⌂
        </span>
        <span className="sidebar__text">HQ</span>
      </NavLink>
      <NavLink to="/projects" className="sidebar__link">
        <span className="sidebar__icon" aria-hidden="true">
          ▣
        </span>
        <span className="sidebar__text">PROJETS</span>
      </NavLink>
      <ul className="sidebar__soon-list">
        {SOON_ITEMS.map((item) => (
          <li key={item.id}>
            <div
              className="sidebar__soon"
              aria-disabled="true"
              title={`${item.label} — bientôt`}
            >
              <span className="sidebar__icon" aria-hidden="true">
                {item.icon}
              </span>
              <span className="sidebar__text">{item.label}</span>
              <span className="sidebar__soon-label">Bientôt</span>
            </div>
          </li>
        ))}
      </ul>
    </nav>
  );
}
