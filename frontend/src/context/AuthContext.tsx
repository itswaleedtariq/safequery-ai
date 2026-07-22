import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  getAccessToken,
  getCurrentUser,
  loginUser,
  removeAccessToken,
  saveAccessToken,
  signupUser,
} from "../api";

import type { AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;

  login: (
    email: string,
    password: string,
  ) => Promise<void>;

  signup: (
    name: string,
    email: string,
    password: string,
  ) => Promise<void>;

  logout: () => void;
}

const AuthContext =
  createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [loading, setLoading] =
    useState(true);

  const clearSession = useCallback(() => {
    removeAccessToken();
    setUser(null);
  }, []);

  useEffect(() => {
    let componentMounted = true;

    async function restoreSession() {
      const token = getAccessToken();

      if (!token) {
        if (componentMounted) {
          setLoading(false);
        }

        return;
      }

      try {
        const currentUser =
          await getCurrentUser();

        if (componentMounted) {
          setUser(currentUser);
        }
      } catch {
        clearSession();
      } finally {
        if (componentMounted) {
          setLoading(false);
        }
      }
    }

    function handleUnauthorized() {
      clearSession();
    }

    window.addEventListener(
      "safequery:unauthorized",
      handleUnauthorized,
    );

    void restoreSession();

    return () => {
      componentMounted = false;

      window.removeEventListener(
        "safequery:unauthorized",
        handleUnauthorized,
      );
    };
  }, [clearSession]);

  const login = useCallback(
    async (
      email: string,
      password: string,
    ): Promise<void> => {
      const response = await loginUser(
        email.trim().toLowerCase(),
        password,
      );

      saveAccessToken(
        response.access_token,
      );

      setUser(response.user);
    },
    [],
  );

  const signup = useCallback(
    async (
      name: string,
      email: string,
      password: string,
    ): Promise<void> => {
      const response = await signupUser(
        name.trim(),
        email.trim().toLowerCase(),
        password,
      );

      saveAccessToken(
        response.access_token,
      );

      setUser(response.user);
    },
    [],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  const contextValue = useMemo(
    () => ({
      user,
      loading,
      login,
      signup,
      logout,
    }),
    [
      user,
      loading,
      login,
      signup,
      logout,
    ],
  );

  return (
    <AuthContext.Provider
      value={contextValue}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider.",
    );
  }

  return context;
}