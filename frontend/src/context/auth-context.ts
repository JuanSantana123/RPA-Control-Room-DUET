import { createContext } from "react";

export interface AuthUser {
    id: number;
    username: string;
    name: string;
    is_active: number;
    permissions: string[];
}

export interface AuthContextValue {
    user: AuthUser | null;
    loading: boolean;
    can: (permission: string) => boolean;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(
    undefined
);
