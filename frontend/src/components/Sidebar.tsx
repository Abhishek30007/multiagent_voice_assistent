import React from 'react';
import { 
  LayoutDashboard, 
  Mail, 
  Calendar, 
  PhoneCall, 
  Activity, 
  Settings,
  PhoneForwarded
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  openVoiceTester: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, openVoiceTester }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'emails', label: 'Imported Emails', icon: Mail },
    { id: 'calendar', label: 'Calendar Schedule', icon: Calendar },
    { id: 'calls', label: 'Call History', icon: PhoneCall },
    { id: 'monitor', label: 'Agent Monitor', icon: Activity },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <PhoneForwarded size={22} />
        <span>Abhishek AI Twin</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={`nav-item ${currentTab === item.id ? 'active' : ''}`}
              onClick={() => setCurrentTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto', padding: '20px' }}>
        <button 
          className="btn btn-primary" 
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={openVoiceTester}
        >
          <PhoneCall size={16} />
          <span>Test Voice Call</span>
        </button>
      </div>
    </aside>
  );
};
