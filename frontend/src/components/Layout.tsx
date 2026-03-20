import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import ChatSidebar from './ChatSidebar';

export default function Layout() {
  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">
        <Outlet />
      </main>
      <ChatSidebar />
    </div>
  );
}
