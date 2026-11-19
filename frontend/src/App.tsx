import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { VoiceTesterModal } from './components/VoiceTesterModal';
import { OverviewPage } from './pages/OverviewPage';
import { EmailsPage } from './pages/EmailsPage';
import { CalendarPage } from './pages/CalendarPage';
import { CallHistoryPage } from './pages/CallHistoryPage';
import { AgentMonitorPage } from './pages/AgentMonitorPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [voiceTesterOpen, setVoiceTesterOpen] = useState<boolean>(false);

  const renderContent = () => {
    switch (currentTab) {
      case 'overview':
        return <OverviewPage />;
      case 'emails':
        return <EmailsPage />;
      case 'calendar':
        return <CalendarPage />;
      case 'calls':
        return <CallHistoryPage />;
      case 'monitor':
        return <AgentMonitorPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        openVoiceTester={() => setVoiceTesterOpen(true)}
      />

      <main className="main-content">
        <header className="topbar">
          <h1 className="topbar-title">Personal AI Twin Dashboard</h1>
          <button 
            className="btn btn-primary"
            onClick={() => setVoiceTesterOpen(true)}
          >
            Launch Voice Tester
          </button>
        </header>

        <section className="content-body">
          {renderContent()}
        </section>
      </main>

      <VoiceTesterModal
        isOpen={voiceTesterOpen}
        onClose={() => setVoiceTesterOpen(false)}
      />
    </div>
  );
};
export default App;
