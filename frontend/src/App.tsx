import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { RequireRole } from './auth/RequireRole'
import { ROLE_HOME } from './auth/roles'
import { Layout } from './components/Layout'
import { AdminHome } from './pages/AdminHome'
import { CustomerHome } from './pages/CustomerHome'
import { DriverHome } from './pages/DriverHome'
import { LoginPage } from './pages/LoginPage'

function HomeRedirect() {
  const { user, restoring } = useAuth()
  if (restoring) return null
  return <Navigate to={user ? ROLE_HOME[user.role] : '/login'} replace />
}

function NotFound() {
  return (
    <>
      <h1>Page not found</h1>
      <Link to="/">Back home</Link>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomeRedirect />} />
            <Route path="login" element={<LoginPage />} />

            {/* Each role's views nest under its own guarded prefix */}
            <Route path="admin" element={<RequireRole role="admin" />}>
              <Route index element={<AdminHome />} />
            </Route>
            <Route path="driver" element={<RequireRole role="driver" />}>
              <Route index element={<DriverHome />} />
            </Route>
            <Route path="customer" element={<RequireRole role="customer" />}>
              <Route index element={<CustomerHome />} />
            </Route>

            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
