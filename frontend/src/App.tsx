import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import { WardrobeProvider } from './context/WardrobeContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import UploadPage from './pages/UploadPage';
import WardrobePage from './pages/WardrobePage';
import TryOnPage from './pages/TryOnPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ChatProvider>
          <WardrobeProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/wardrobe" element={<WardrobePage />} />
                  <Route path="/tryon" element={<TryOnPage />} />
                </Route>
              </Route>
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </WardrobeProvider>
        </ChatProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
