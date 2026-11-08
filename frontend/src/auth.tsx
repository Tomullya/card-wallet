import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { getToken, request, setToken, setUnauthorizedHandler, type User } from "./api";

interface AuthState {
  user: User | null;
  loading: boolean;
  sessionMessage: string | null;
  login(email: string, password: string): Promise<void>;
  register(email: string, name: string, password: string): Promise<void>;
  logout(): void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(getToken()));
  const [sessionMessage, setSessionMessage] = useState<string | null>(null);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
      setSessionMessage("Session expired — please log in again");
    });
    if (!getToken()) return;
    request<User>("GET", "/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await request<{ access_token: string }>("POST", "/auth/login", {
      email,
      password,
    });
    setToken(access_token);
    setSessionMessage(null);
    setUser(await request<User>("GET", "/me"));
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      await request<User>("POST", "/auth/register", { email, name, password });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, sessionMessage, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const state = useContext(AuthContext);
  if (!state) throw new Error("useAuth must be used inside AuthProvider");
  return state;
}
