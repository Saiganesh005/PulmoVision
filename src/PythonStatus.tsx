import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';

export default function PythonStatus() {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [details, setDetails] = useState<string>('');

  const checkStatus = async () => {
    try {
      const response = await fetch('/api/admin/check-python');
      if (response.ok) {
        const data = await response.json();
        const hasTorch = data.stdout.includes('torch');
        const hasKaggle = data.stdout.includes('kaggle');
        
        if (hasTorch && hasKaggle) {
          setStatus('ready');
        } else {
          setStatus('error');
          setDetails('Missing core dependencies (torch/kaggle)');
        }
      } else {
        setStatus('error');
        setDetails('Failed to check Python status');
      }
    } catch (error) {
      setStatus('error');
      setDetails('Network error checking Python');
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-3 bg-[var(--bg-color)]/50 rounded-lg border border-[var(--primary-color)]/30 flex items-center gap-3">
      {status === 'loading' && <Loader2 className="animate-spin text-[var(--primary-color)]" size={16} />}
      {status === 'ready' && <CheckCircle className="text-green-500" size={16} />}
      {status === 'error' && <XCircle className="text-red-500" size={16} />}
      
      <div className="flex flex-col flex-1">
        <span className="text-[10px] uppercase tracking-widest font-bold">Python Engine</span>
        <span className="text-[8px] text-[var(--secondary-text)] truncate max-w-[120px]">
          {status === 'loading' ? 'Initializing...' : status === 'ready' ? 'Ready' : details}
        </span>
      </div>
      
      <button 
        onClick={() => {
          setStatus('loading');
          checkStatus();
        }}
        className="ml-auto text-[var(--primary-color)] hover:opacity-70 transition-opacity"
        title="Refresh Python Status"
      >
        <RefreshCw size={14} className={status === 'loading' ? 'animate-spin' : ''} />
      </button>

      {status === 'error' && (
        <button 
          onClick={() => {
            setStatus('loading');
            fetch('/api/admin/install-python');
            setTimeout(checkStatus, 5000);
          }}
          className="ml-2 text-[8px] font-bold text-[var(--primary-color)] hover:underline uppercase"
        >
          Retry
        </button>
      )}
    </div>
  );
}
