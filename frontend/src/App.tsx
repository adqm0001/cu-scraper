import { Login } from './pages/Login.tsx'
import { Register } from './pages/Register.tsx'
import { Dashboard } from './pages/Dashboard.tsx'
import { AuthProvider } from './context/AuthContext.tsx'
import { ProtectedLayout } from './layouts/ProtectedLayout.tsx' 
import { BrowserRouter, Routes, Route } from 'react-router';
import {Navigate, Outlet} from 'react-router';

export function AuthLayout() { return <Outlet /> }
export function Profile() { return <div>Profile</div> }

function App() {
  return (
    <>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route index element={<Navigate to="/login" />} />
          <Route element={<AuthLayout />}>
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
          </Route>
          <Route path="app" element={<ProtectedLayout />}>
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="profile" element={<Profile />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </>
  )
}

export default App;
