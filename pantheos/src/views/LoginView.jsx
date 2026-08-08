import { LogIn, ShieldAlert } from "lucide-react";
import { CSS } from "../styles.js";

const wrap = {
  minHeight: "100vh", background: "var(--paper)", display: "flex",
  alignItems: "center", justifyContent: "center", padding: 24,
};
const card = {
  background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 14,
  padding: "34px 32px", width: 360, textAlign: "center",
};

function Mark() {
  return (
    <div className="gs-brand-mark" style={{ margin: "0 auto 16px" }}>
      <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
        <path d="M16 4 27.5 11.5 4.5 11.5Z" fill="#1F9D62" />
        <rect x="8" y="12.4" width="4.6" height="15.2" fill="#fff" />
        <rect x="19.4" y="12.4" width="4.6" height="15.2" fill="#fff" />
      </svg>
    </div>
  );
}

export default function LoginView({ booting, denied, email, error, onSignIn, onSignOut }) {
  let body;
  if (booting) {
    body = <div className="gs-empty" style={{ padding: 0 }}>Establishing link…</div>;
  } else if (denied) {
    body = (
      <>
        <div className="gs-eyebrow" style={{ color: "var(--fault)" }}>ACCESS DENIED</div>
        <h1 className="gs-h1">Not authorized</h1>
        <p className="gs-sub">
          Signed in as {email}. This account is not on the Pantheos allowlist.
        </p>
        <button className="gs-btn ghost" onClick={onSignOut} style={{ width: "100%", justifyContent: "center" }}>
          <ShieldAlert size={15} />Sign out
        </button>
      </>
    );
  } else {
    body = (
      <>
        <div className="gs-eyebrow">PANTHEOS // LIFE OS</div>
        <h1 className="gs-h1">Authentication required</h1>
        <p className="gs-sub">Sign in to reach the queue, projects, monitor, and Delphi.</p>
        <button className="gs-btn primary" onClick={onSignIn} style={{ width: "100%", justifyContent: "center" }}>
          <LogIn size={15} />Sign in with Google
        </button>
        {error && (
          <p className="gs-sub" style={{ color: "var(--fault)", margin: "14px 0 0", fontSize: 12.5 }}>{error}</p>
        )}
      </>
    );
  }
  return (
    <div className="gs">
      <style>{CSS}</style>
      <div style={wrap}><div style={card}><Mark />{body}</div></div>
    </div>
  );
}
