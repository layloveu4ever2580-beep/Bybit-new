import React, { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, Clock, CheckCircle, XCircle } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function Dashboard() {
  const [trades, setTrades] = useState([]);
  const [settings, setSettings] = useState({ target_profit: 60, timezone: 'UTC', theme: 'dark' });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState('All');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Auto-sync every 60s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.theme]);

  const fetchData = async () => {
    try {
      const [tradesRes, settingsRes] = await Promise.all([
        fetch(`${API_BASE}/trades`),
        fetch(`${API_BASE}/settings`)
      ]);
      const tradesData = await tradesRes.json();
      const settingsData = await settingsRes.json();
      
      if (Array.isArray(tradesData)) setTrades(tradesData);
      if (settingsData && settingsData.target_profit) setSettings(settingsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const syncTrades = async () => {
    setSyncing(true);
    try {
      await fetch(`${API_BASE}/sync-trades`, { method: 'POST' });
      await fetchData();
    } catch (error) {
      console.error('Error syncing:', error);
    } finally {
      setSyncing(false);
    }
  };

  const updateSetting = async (key: string, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    try {
      await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings),
      });
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const toggleTheme = () => {
    updateSetting('theme', settings.theme === 'dark' ? 'light' : 'dark');
  };

  const totalPnL = trades.reduce((acc, trade) => acc + (trade.pnl || 0), 0);
  const monthlyPnL = trades
    .filter(t => new Date(t.created_at).getMonth() === new Date().getMonth())
    .reduce((acc, trade) => acc + (trade.pnl || 0), 0);
  const closedTrades = trades.filter(t => t.status === 'closed');
  const winningTrades = closedTrades.filter(t => (t.pnl || 0) > 0);
  const winRate = closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0;
  const activePositions = trades.filter(t => t.status === 'open').length;

  const filteredTrades = trades.filter(t => {
    if (filter === 'All') return true;
    return t.status.toLowerCase() === filter.toLowerCase();
  });

  return (
    <div className="max-w-7xl mx-auto p-6 transition-colors duration-200">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-purple-600">Bybit Trading Bot</h1>
        <div className="flex gap-4">
          <button 
            onClick={toggleTheme}
            className="px-4 py-2 rounded shadow bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
          >
            {settings.theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </button>
          <button 
            onClick={syncTrades}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition shadow-lg shadow-blue-500/30 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            Sync Trades
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <MetricCard title="Total PnL" value={`$${totalPnL.toFixed(2)}`} isPositive={totalPnL >= 0} />
        <MetricCard title="Monthly PnL" value={`$${monthlyPnL.toFixed(2)}`} isPositive={monthlyPnL >= 0} />
        <MetricCard title="Win Rate" value={`${winRate.toFixed(1)}%`} subtext={`${winningTrades.length}/${closedTrades.length}`} neutral />
        <MetricCard title="Active Positions" value={activePositions} neutral />
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl overflow-hidden shadow-gray-200/50 dark:shadow-none border border-gray-100 dark:border-gray-700">
        <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center">
          <h2 className="text-xl font-semibold">Trade History</h2>
          <div className="flex gap-2">
            {['All', 'Open', 'Closed', 'Failed'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                  filter === f 
                    ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300' 
                    : 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Time</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Pair</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Action</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Entry</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Target</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">PnL</th>
                <th className="p-4 font-medium text-gray-500 dark:text-gray-400">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {loading ? (
                <tr><td colSpan={7} className="p-8 text-center text-gray-500">Loading trades...</td></tr>
              ) : filteredTrades.length === 0 ? (
                <tr><td colSpan={7} className="p-8 text-center text-gray-500">No trades found.</td></tr>
              ) : (
                filteredTrades.map((trade: any) => (
                  <tr key={trade.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                    <td className="p-4 text-sm">{new Date(trade.created_at).toLocaleString()}</td>
                    <td className="p-4 font-medium">{trade.ticker}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                        trade.action === 'buy' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}>
                        {trade.action}
                      </span>
                    </td>
                    <td className="p-4">${trade.entry_price?.toFixed(4) || '-'}</td>
                    <td className="p-4 font-medium text-blue-600 dark:text-blue-400">${trade.target_profit?.toFixed(2) || '0.00'}</td>
                    <td className={`p-4 font-medium ${trade.pnl > 0 ? 'text-green-500' : trade.pnl < 0 ? 'text-red-500' : ''}`}>
                      {trade.pnl ? `${trade.pnl > 0 ? '+' : ''}$${trade.pnl.toFixed(2)}` : '-'}
                    </td>
                    <td className="p-4">
                      <StatusBadge status={trade.status} error={trade.error_msg} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const MetricCard = ({ title, value, isPositive, neutral, subtext }: any) => {
  const color = neutral ? 'text-blue-500 dark:text-blue-400' : isPositive ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400';
  const Icon = neutral ? Clock : isPositive ? TrendingUp : TrendingDown;
  
  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-xl shadow-gray-200/50 dark:shadow-none border border-gray-100 dark:border-gray-700 flex flex-col justify-between">
      <h3 className="text-gray-500 dark:text-gray-400 font-medium mb-2">{title}</h3>
      <div className="flex items-end justify-between">
        <div>
          <span className={`text-3xl font-bold ${color}`}>{value}</span>
          {subtext && <span className="ml-2 text-sm text-gray-500">{subtext}</span>}
        </div>
        <Icon className={`w-6 h-6 ${color} opacity-50`} />
      </div>
    </div>
  );
}

const StatusBadge = ({ status, error }: any) => {
  if (status === 'open') return <span className="flex items-center gap-1 text-sm text-blue-500"><Clock className="w-4 h-4"/> Open</span>;
  if (status === 'closed') return <span className="flex items-center gap-1 text-sm text-green-500"><CheckCircle className="w-4 h-4"/> Closed</span>;
  return (
    <div title={error} className="flex items-center gap-1 text-sm text-red-500 cursor-help">
      <XCircle className="w-4 h-4"/> Failed
    </div>
  );
}
