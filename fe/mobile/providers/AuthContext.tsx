import { createContext } from 'react';
export type AuthDatatype = {
    user_id: number;
    email: string;
}
export type AuthContextType = {
    user: AuthDatatype | null
    setUser: (user: AuthDatatype | null) => void;
    loading: boolean;
    setLoading: (loading: boolean) => void;
}
export const AuthContext = createContext<AuthContextType | undefined>(undefined);