import React, { useState } from 'react';
import { Search, Eye, Filter } from 'lucide-react';

export default function HistoryPage({ history, clearHistory, isClearing, successMessage, onViewResults }: { history: any[], clearHistory: () => void, isClearing: boolean, successMessage: string | null, onViewResults: (id: number) => void }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('All');
  const [sortBy, setSortBy] = useState('date-desc');
  const [showConfirm, setShowConfirm] = useState(false);

  const filteredData = history.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          item.disease.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === 'All' || 
                          (filter === 'Normal' && item.disease === 'NORMAL') || 
                          (filter === 'Diseased' && item.disease !== 'NORMAL');
    return matchesSearch && matchesFilter;
  }).sort((a, b) => {
    if (sortBy === 'date-desc') return new Date(b.date).getTime() - new Date(a.date).getTime();
    if (sortBy === 'date-asc') return new Date(a.date).getTime() - new Date(b.date).getTime();
    if (sortBy === 'name-asc') return a.name.localeCompare(b.name);
    return 0;
  });

  return (
    <div className="p-8 max-w-6xl mx-auto text-[var(--text-color)] font-serif">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-color)]">Patient History</h1>
        <button 
          onClick={() => setShowConfirm(true)} 
          disabled={history.length === 0 || isClearing}
          className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-all font-bold shadow-md"
        >
          {isClearing ? 'Clearing...' : 'Clear All Records'}
        </button>
      </div>

      {successMessage && (
        <div className="bg-green-100 text-green-800 p-4 rounded-lg mb-6">{successMessage}</div>
      )}

      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 text-[var(--secondary-text)]" size={20} />
          <input 
            type="text" 
            placeholder="Search by name or diagnosis..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 p-3 bg-[var(--bg-color)] rounded-lg border-2 border-[var(--primary-color)] text-[var(--text-color)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-color)]/50"
          />
        </div>
        <select 
          value={filter} 
          onChange={(e) => setFilter(e.target.value)}
          className="p-3 bg-[var(--bg-color)] rounded-lg border-2 border-[var(--primary-color)] text-[var(--text-color)]"
        >
          <option value="All">All Status</option>
          <option value="Normal">Normal</option>
          <option value="Diseased">Diseased</option>
        </select>
        <select 
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value)}
          className="p-3 bg-[var(--bg-color)] rounded-lg border-2 border-[var(--primary-color)] text-[var(--text-color)]"
        >
          <option value="date-desc">Newest First</option>
          <option value="date-asc">Oldest First</option>
          <option value="name-asc">Name A-Z</option>
        </select>
      </div>

      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-[var(--card-bg)] p-8 rounded-xl border-2 border-[var(--primary-color)] shadow-2xl max-w-md w-full">
            <h2 className="text-xl font-bold mb-4 text-[var(--text-color)]">Clear All Records?</h2>
            <p className="mb-6 text-[var(--secondary-text)]">This action will permanently delete all patient history records. This cannot be undone.</p>
            <div className="flex justify-end gap-4">
              <button 
                onClick={() => setShowConfirm(false)} 
                className="px-6 py-2 rounded-lg border border-[var(--primary-color)] text-[var(--text-color)] hover:bg-[var(--primary-color)]/10 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={() => { clearHistory(); setShowConfirm(false); }} 
                className="px-6 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors font-bold shadow-lg"
              >
                Yes, Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {history.length === 0 ? (
        <div className="text-center p-16 bg-[var(--bg-color)] rounded-xl border-2 border-dashed border-[var(--primary-color)]">
          <div className="flex justify-center mb-4">
            <Search size={48} className="text-[var(--secondary-text)] opacity-50" />
          </div>
          <p className="text-2xl font-bold text-[var(--text-color)]">No data available</p>
          <p className="text-[var(--secondary-text)] mt-2 italic">Train or test the model to view results</p>
        </div>
      ) : (
        <div className="overflow-x-auto bg-[var(--card-bg)] rounded-xl border-2 border-[var(--primary-color)] shadow-lg">
          <table className="w-full text-left">
            <thead className="bg-[var(--primary-color)]/10 sticky top-0">
              <tr>
                <th className="p-4 text-[var(--text-color)]">S.No</th>
                <th className="p-4 text-[var(--text-color)]">Date</th>
                <th className="p-4 text-[var(--text-color)]">Patient Name</th>
                <th className="p-4 text-[var(--text-color)]">Age/Gender</th>
                <th className="p-4 text-[var(--text-color)]">Diagnosis</th>
                <th className="p-4 text-[var(--text-color)]">Outcome</th>
                <th className="p-4 text-[var(--text-color)]">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((item, index) => (
                <tr key={item.id} className="border-t border-[var(--primary-color)]/20 hover:bg-[var(--primary-color)]/5 transition-colors">
                  <td className="p-4 text-[var(--text-color)]">{index + 1}</td>
                  <td className="p-4 text-sm text-[var(--secondary-text)]">{item.date}</td>
                  <td className="p-4 font-bold text-[var(--text-color)]">{item.name}</td>
                  <td className="p-4 text-sm text-[var(--secondary-text)]">{item.age} / {item.gender}</td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      item.disease === 'NORMAL' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 
                      item.disease === 'TEST_RESULT' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                      'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                    }`}>
                      {item.disease}
                    </span>
                  </td>
                  <td className="p-4 text-sm italic text-[var(--secondary-text)]">{item.outcome || 'Pending'}</td>
                  <td className="p-4">
                    <button onClick={() => onViewResults(item.id)} className="flex items-center gap-2 text-[var(--primary-color)] hover:underline font-bold">
                      <Eye size={16} /> View Results
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
