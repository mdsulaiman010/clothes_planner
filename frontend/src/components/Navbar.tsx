import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">Digital Closet</div>
      <div className="navbar-links">
        <NavLink to="/upload" className={({ isActive }) => (isActive ? 'active' : '')}>
          Upload
        </NavLink>
        <NavLink to="/wardrobe" className={({ isActive }) => (isActive ? 'active' : '')}>
          Wardrobe
        </NavLink>
        <NavLink to="/tryon" className={({ isActive }) => (isActive ? 'active' : '')}>
          Try On
        </NavLink>
      </div>
      <div className="navbar-user">
        <span>{username}</span>
        <button onClick={handleLogout} className="btn btn-sm">
          Logout
        </button>
      </div>
    </nav>
  );
}
