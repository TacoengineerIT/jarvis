import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Intelligence from './pages/Intelligence'
import Financial from './pages/Financial'
import Academic from './pages/Academic'
import System from './pages/System'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"          element={<Intelligence />} />
        <Route path="/financial" element={<Financial />} />
        <Route path="/academic"  element={<Academic />} />
        <Route path="/system"    element={<System />} />
      </Routes>
    </BrowserRouter>
  )
}
