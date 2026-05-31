import {createContext, useContext, useState, ReactNode} from 'react'

interface AuthContextType {
  token: string;
  setToken: (token: string) => void;
}
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({children}: {children: ReactNode}) {
  const [token, setToken] = useState(localStorage.getItem('token') ?? '');
  
  return(
  <AuthContext value={{token, setToken}}>
    {children}
  </AuthContext>
  )

}
export function useAuthContext() {

  const authCtx = useContext(AuthContext);
  if (authCtx === undefined){
    throw new Error('useAuthContext must be used within an AuthProvider');
  }

  return authCtx;
}
