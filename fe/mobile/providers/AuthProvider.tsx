import { useState } from "react";
import { useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthContext, AuthDatatype } from "./AuthContext";
import { api } from '@/services/api';
export default function AuthProvider({children}: {children: React.ReactNode}){
    const [ user, setUser ] = useState<AuthDatatype | null>(null);
    const [ loading, setLoading ] = useState<boolean>(true);

    useEffect(() => {
        let isMounted = true;

        const restoreSession = async () => {
            try {
                const token = await AsyncStorage.getItem('accessToken');
                if (!token) {
                    if (isMounted) {
                        setUser(null);
                    }
                    return;
                }

                const me = await api.getMe();
                if (isMounted) {
                    setUser({
                        user_id: me.user_id,
                        email: me.email,
                    });
                }
            } catch (error) {
                await AsyncStorage.removeItem('accessToken');
                if (isMounted) {
                    setUser(null);
                }
            } finally {
                if (isMounted) {
                    setLoading(false);
                }
            }
        };

        restoreSession();

        return () => {
            isMounted = false;
        };
    }, []);

    return (
        <AuthContext.Provider value={{user, setUser, loading, setLoading}}>
            {children}
        </AuthContext.Provider>

    )
}
