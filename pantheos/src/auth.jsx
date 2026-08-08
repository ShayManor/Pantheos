import { createContext, useContext, useEffect, useState } from "react";
import { initializeApp } from "firebase/app";
import { GoogleAuthProvider, getAuth, onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { api, setOnAuthFailure, setTokenProvider } from "./api.js";
import LoginView from "./views/LoginView.jsx";

// Off means the gate is down (local dev, pytest, E2E) and the app renders as it
// always has, so useAuth() has to answer safely for consumers either way.
const Ctx = createContext({ user: null, signOut: () => {} });
export const useAuth = () => useContext(Ctx);

let fbAuth = null;  // one Firebase app per page load, however often the effect runs

export function AuthProvider({ children }) {
  const [cfg, setCfg] = useState(null);         // null while asking the API
  const [user, setUser] = useState(undefined);  // undefined while Firebase resolves
  const [access, setAccess] = useState(null);   // "ok" | "denied" once probed
  const [error, setError] = useState(null);

  // The gate state is not knowable without the API, so a failed config fetch
  // must not resolve to "off" — that would mount the app unguarded. Hold the
  // boot screen and retry until the API answers.
  useEffect(() => {
    let live = true;
    let timer = null;
    const load = () => {
      fetch("/api/auth/config")
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
        .then((c) => { if (live) setCfg(c); })
        .catch(() => { if (live) timer = setTimeout(load, 2000); });
    };
    load();
    return () => { live = false; clearTimeout(timer); };
  }, []);

  useEffect(() => {
    if (!cfg?.enabled) return;
    if (!fbAuth) {
      fbAuth = getAuth(initializeApp({
        apiKey: cfg.apiKey, authDomain: cfg.authDomain, projectId: cfg.projectId,
      }));
    }
    setTokenProvider(() => fbAuth.currentUser?.getIdToken() ?? null);
    setOnAuthFailure(() => signOut(fbAuth));
    return onAuthStateChanged(fbAuth, (u) => { setUser(u); setAccess(null); });
  }, [cfg]);

  // The allowlist lives on the server, so ask it before mounting the app. A
  // stranger with a valid Google account gets told, not shown an empty shell.
  useEffect(() => {
    if (!user) return;
    let live = true;
    let timer = null;
    const probe = () => {
      api.authMe()
        .then(() => { if (live) setAccess("ok"); })
        .catch((e) => {
          if (!live) return;
          // Only the server saying "not allowlisted" is a denial. Anything else
          // is transient: hold the boot screen rather than accusing the user.
          if (e.status === 403) setAccess("denied");
          else timer = setTimeout(probe, 2000);
        });
    };
    probe();
    return () => { live = false; clearTimeout(timer); };
  }, [user]);

  if (!cfg) return <LoginView booting />;
  if (!cfg.enabled) return children;
  if (user === undefined) return <LoginView booting />;
  if (!user) {
    return (
      <LoginView
        error={error}
        onSignIn={() => {
          setError(null);
          signInWithPopup(fbAuth, new GoogleAuthProvider())
            .catch((e) => setError(e.code || "sign-in failed"));
        }}
      />
    );
  }
  if (access === null) return <LoginView booting />;
  if (access === "denied") {
    return <LoginView denied email={user.email} onSignOut={() => signOut(fbAuth)} />;
  }
  return (
    <Ctx.Provider value={{ user, signOut: () => signOut(fbAuth) }}>{children}</Ctx.Provider>
  );
}
