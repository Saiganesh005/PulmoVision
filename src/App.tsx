/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { LayoutGrid, Upload, FileText, Settings as SettingsIcon, User, Activity, History, LogOut, FlaskConical, Microscope } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from './services/firebase';
import Settings from './Settings';
import TestingPage from './TestingPage';
import AnalysisPage from './AnalysisPage';
import AccountProfile from './AccountProfile';
import HistoryPage from './HistoryPage';
import LoginPage from './LoginPage';
import PythonStatus from './PythonStatus';
import { ThemeProvider } from './ThemeContext';

const diseases = [
  "NORMAL", "PNEUMONIA", "LUNG OPACITY", "PLEURAL EFFUSION", "LUNG CANCER", 
  "LUNG INFECTION", "PNEUMOTHORAX", "EMPHYSEMA", "PULMONARY FIBROSIS"
];

const navItems = [
  { name: 'Dashboard', icon: LayoutGrid },
  { name: 'Testing', icon: FlaskConical },
  { name: 'Analysis', icon: Microscope },
  { name: 'History', icon: History },
  { name: 'Preferences', icon: SettingsIcon },
];

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [logo, setLogo] = useState<string | null>(localStorage.getItem('logo'));
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activePage, setActivePage] = useState('Dashboard');
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isClearing, setIsClearing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  React.useEffect(() => {
    if (logo) localStorage.setItem('logo', logo);
    else localStorage.removeItem('logo');
  }, [logo]);

  const handleLogout = async () => {
    await signOut(auth);
    localStorage.removeItem('logo');
    setLogo(null);
  };

  const clearHistory = async () => {
    setIsClearing(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setHistory([]);
    setIsClearing(false);
    setSuccessMessage("History cleared successfully");
    setTimeout(() => setSuccessMessage(null), 3000);
    console.log("History, training, and testing data cleared.");
  };

  if (loading) return <div className="h-screen flex items-center justify-center">Loading...</div>;

  if (!user) {
    return <LoginPage onLogin={() => {}} />;
  }

  const renderPage = () => {
    switch (activePage) {
      case 'Preferences':
        return <Settings />;
      case 'Testing':
        return <TestingPage setUploadedImage={setUploadedImage} setActivePage={setActivePage} />;
      case 'Analysis':
        return <AnalysisPage uploadedImage={uploadedImage} setUploadedImage={setUploadedImage} addToHistory={(item) => setHistory(prev => [item, ...prev])} />;
      case 'History':
        return <HistoryPage history={history} clearHistory={clearHistory} isClearing={isClearing} successMessage={successMessage} onViewResults={() => setActivePage('Analysis')} />;
      case 'Account Profile':
        return <AccountProfile user={user} logo={logo} setLogo={setLogo} />;
      default:
        return (
          <>
            <header className="mb-8 flex justify-between items-center">
              <h1 className="text-3xl font-bold text-black dark:text-dark-mode-green">Dashboard</h1>
              <div className="text-lg font-bold text-black dark:text-dark-mode-green font-mono">{time}</div>
            </header>

            {/* Summary Cards */}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div className="bg-gray-100 dark:bg-gray-900 p-6 rounded-xl border-2 border-gray-300 dark:border-dark-mode-green">
                <h3 className="text-black dark:text-dark-mode-green">Total Scans</h3>
                <p className="text-4xl font-bold text-black dark:text-dark-mode-green">{history.length}</p>
              </div>
              <div className="bg-gray-100 dark:bg-gray-900 p-6 rounded-xl border-2 border-gray-300 dark:border-dark-mode-green">
                <h3 className="text-black dark:text-dark-mode-green">Normal Cases</h3>
                <p className="text-4xl font-bold text-black dark:text-dark-mode-green">{history.filter(h => h.disease === 'NORMAL').length}</p>
              </div>
            </section>

            {/* Disease Grid */}
            <section>
              <h2 className="text-xl font-semibold mb-4 text-black dark:text-dark-mode-green">Lung Disease Analysis</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {diseases.map((disease) => {
                  const count = history.filter(h => h.disease === disease).length;
                  return (
                    <div key={disease} className={`bg-gray-100 dark:bg-gray-900 p-4 rounded-lg border-2 ${disease === 'NORMAL' ? 'border-emerald-500 dark:border-emerald-500' : 'border-red-500 dark:border-red-500'} hover:border-teal-600 dark:hover:border-teal-500 transition-colors`}>
                      <p className={`text-xs ${disease === 'NORMAL' ? 'text-emerald-500' : 'text-red-500'} truncate`}>{disease}</p>
                      <p className={`text-2xl font-bold ${disease === 'NORMAL' ? 'text-emerald-500' : 'text-red-500'}`}>{count}</p>
                    </div>
                  );
                })}
              </div>
            </section>
          </>
        );
    }
  };

  return (
    <div className="flex h-screen bg-[var(--bg-color)] text-[var(--text-color)] font-serif font-bold">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: isSidebarOpen ? 240 : 80 }}
        className="bg-[var(--card-bg)] border-r-2 border-[var(--primary-color)] flex flex-col p-4"
      >
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-[var(--primary-color)]/20 rounded-lg">
            {logo ? (
              <img src={logo} alt="Logo" className="w-8 h-8 rounded-full" />
            ) : (
              <div className="w-8 h-8 bg-[var(--primary-color)] rounded-full flex items-center justify-center text-white font-bold">L</div>
            )}
          </button>
          {isSidebarOpen && (
            <span className="font-bold text-[var(--text-color)] text-lg">MedScan AI</span>
          )}
        </div>

        <nav className="flex-1 space-y-2">
          {navItems.map((item) => (
            <button key={item.name} onClick={() => setActivePage(item.name)} className="w-full flex items-center gap-4 p-3 hover:bg-[var(--primary-color)]/20 rounded-lg border border-[var(--primary-color)] text-[var(--text-color)]">
              <item.icon size={20} />
              {isSidebarOpen && <span>{item.name}</span>}
            </button>
          ))}
        </nav>

        {isSidebarOpen && (
          <div className="mb-4">
            <PythonStatus />
          </div>
        )}

        <div className="mt-auto border-t-2 border-[var(--primary-color)] pt-4 space-y-2">
          <button onClick={() => setActivePage('Account Profile')} className="w-full flex items-center gap-4 p-3 hover:bg-[var(--primary-color)]/20 rounded-lg border border-[var(--primary-color)] text-[var(--text-color)]">
            <User size={20} />
            {isSidebarOpen && <span>Account Profile</span>}
          </button>
          <button onClick={handleLogout} className="w-full flex items-center gap-4 p-3 hover:bg-red-900/20 rounded-lg border border-red-800 text-red-400">
            <LogOut size={20} />
            {isSidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="border-2 border-[var(--primary-color)] rounded-2xl p-6 h-full overflow-y-auto bg-[var(--card-bg)]">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}

