import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom'
import NavigationDrawer from './components/NavigationDrawer'
import Intelligence from './pages/Intelligence'
import Dashboard from './pages/Dashboard'
import Financial from './pages/Financial'
import Academic from './pages/Academic'
import System from './pages/System'

function SharedLayout() {
  return (
    <>
      <NavigationDrawer />
      <Outlet />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Intelligence />} />
        <Route element={<SharedLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/financial" element={<Financial />} />
          <Route path="/academic" element={<Academic />} />
          <Route path="/system" element={<System />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
