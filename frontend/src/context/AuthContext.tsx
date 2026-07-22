import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { LocalUser } from "../types";

interface StoredAccount extends LocalUser {
  passwordHash: string;
}

interface AuthContextValue {
  user: LocalUser | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    name: string,
    email: string,
    password: string,
  ) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const ACCOUNT_KEY = "safequery.localAccount";
const SESSION_KEY = "safequery.session";

async function hashPassword(password: string): Promise<string> {
  const bytes = new TextEncoder().encode(password);
  const digest = await crypto.subtle.digest("SHA-256", bytes);

  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function readSession(): LocalUser | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? (JSON.parse(raw) as LocalUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<LocalUser | null>(readSession);

  async function signup(
    name: string,
    email: string,
    password: string,
  ): Promise<void> {
    const normalizedEmail = email.trim().toLowerCase();
    const account: StoredAccount = {
      name: name.trim(),
      email: normalizedEmail,
      passwordHash: await hashPassword(password),
    };

    localStorage.setItem(ACCOUNT_KEY, JSON.stringify(account));

    const session: LocalUser = {
      name: account.name,
      email: account.email,
    };

    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    setUser(session);
  }

  async function login(email: string, password: string): Promise<void> {
    const raw = localStorage.getItem(ACCOUNT_KEY);

    if (!raw) {
      throw new Error("No account exists on this browser. Create one first.");
    }

    const account = JSON.parse(raw) as StoredAccount;
    const passwordHash = await hashPassword(password);

    if (
      account.email !== email.trim().toLowerCase() ||
      account.passwordHash !== passwordHash
    ) {
      throw new Error("Email or password is incorrect.");
    }

    const session: LocalUser = {
      name: account.name,
      email: account.email,
    };

    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    setUser(session);
  }

  function logout(): void {
    localStorage.removeItem(SESSION_KEY);
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, login, signup, logout }),
    [user],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return value;
}