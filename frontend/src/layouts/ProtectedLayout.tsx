import { useAuthContext } from "../context/AuthContext.tsx";
import {Navigate, Outlet} from 'react-router';

export function ProtectedLayout() {
  const {token} = useAuthContext();

  if (!token) {
    return <Navigate to="/login" replace/> 
  }

  return <Outlet />;
}
