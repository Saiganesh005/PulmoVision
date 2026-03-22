import React, { useState } from 'react';
import { Palette, Globe, Clock, Save } from 'lucide-react';
import { useTheme } from './ThemeContext';

export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const [language, setLanguage] = useState('English');
  const [timeZone, setTimeZone] = useState('Asia/Kolkata');
  const [message, setMessage] = useState('');

  const handleSave = () => {
    localStorage.setItem('settings', JSON.stringify({ language, timeZone }));
    setMessage('Settings updated successfully');
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto text-[var(--text-color)] font-serif font-bold">
      <h1 className="text-3xl font-bold mb-8 text-[var(--text-color)]">Settings</h1>
      
      {message && <div className="mb-4 p-4 bg-green-900/20 border border-[var(--primary-color)] rounded-lg text-[var(--text-color)]">{message}</div>}

      {/* Appearance */}
      <section className="bg-[var(--card-bg)] p-6 rounded-xl border-2 border-[var(--primary-color)] mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Palette className="text-[var(--primary-color)]" />
          <h2 className="text-xl text-[var(--text-color)]">Appearance</h2>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[var(--text-color)]">{theme === 'dark' ? '🌙 Dark Mode' : '☀️ Light Mode'}</span>
          <button 
            onClick={toggleTheme}
            className="bg-[var(--primary-color)] text-[var(--bg-color)] px-4 py-2 rounded-lg"
          >
            Toggle
          </button>
        </div>
      </section>

      {/* Language */}
      <section className="bg-gray-900 p-6 rounded-xl border-2 border-dark-mode-green mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Globe className="text-dark-mode-green" />
          <h2 className="text-xl">Language</h2>
        </div>
        <select 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full bg-gray-800 p-3 rounded-lg border border-dark-mode-green text-dark-mode-green"
        >
          <option>English</option>
          <option>Japanese</option>
          <option>Hindi</option>
          <option>Spanish</option>
          <option>French</option>
        </select>
      </section>

      {/* Time Zone */}
      <section className="bg-gray-900 p-6 rounded-xl border-2 border-dark-mode-green mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Clock className="text-dark-mode-green" />
          <h2 className="text-xl">Time Zone</h2>
        </div>
        <select 
          value={timeZone} 
          onChange={(e) => setTimeZone(e.target.value)}
          className="w-full bg-gray-800 p-3 rounded-lg border border-dark-mode-green text-dark-mode-green"
        >
          <option>Asia/Tokyo</option>
          <option>Asia/Kolkata</option>
          <option>UTC</option>
          <option>America/New_York</option>
          <option>Europe/London</option>
        </select>
      </section>

      <button 
        onClick={handleSave}
        className="flex items-center gap-2 bg-dark-mode-green text-white px-6 py-3 rounded-lg font-bold hover:bg-opacity-90"
      >
        <Save size={20} />
        Save Settings
      </button>
    </div>
  );
}
