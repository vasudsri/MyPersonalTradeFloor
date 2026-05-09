import React, { useState, useEffect } from 'react';
import { Radar, TrendingUp, AlertTriangle, Crosshair, Target, ShieldCheck, ExternalLink, Briefcase, BarChart4, IndianRupee, History } from 'lucide-react';

interface ScannerItem {
  symbol: string;
  rs_rating: number;
  status: string;
  trend: string;
  setup_type: string;
  all_setups: string[];
  is_setup: boolean;
  entry: number;
  stop: number;
  target: number;
  adr: number;
}

interface PortfolioItem {
  symbol: string;
  entry_date: string;
  entry_price: number;
  current_price: number;
  exit_price?: number;
  exit_date?: string;
  stop_loss: number;
  target: number;
  setup_type: string;
  pnl_pct: number;
  status: string;
}

interface StrategyStat {
  total_trades: number;
  win_rate: number;
  total_pnl_pct: number;
  total_pnl_currency: number;
}

interface BattlePlan {
  date: string;
  timestamp: string;
  market_regime: {
    regime: string;
    recommendation: {
        primary: string;
        risk_multiplier: number;
        rationale: string;
    };
  };
  scan_summary: {
    momentum_count?: number;
    reversion_count?: number;
    fundamental_count?: number;
    universe_size: number;
  };
  scanner_data: ScannerItem[];
}

interface PortfolioData {
  active_positions: PortfolioItem[];
  closed_positions: PortfolioItem[];
  stats: {
    total_trades: number;
    win_rate: number;
    total_pnl_pct: number;
    net_pnl_currency: number;
    active_pnl_currency: number;
  };
  strategy_stats: Record<string, StrategyStat>;
}

export function TradingRadarPage() {
  const [data, setData] = useState<BattlePlan | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [planRes, portRes] = await Promise.all([
          fetch('/data/battle_plan.json'),
          fetch('/data/portfolio.json')
        ]);
        
        if (planRes.ok) setData(await planRes.json());
        if (portRes.ok) setPortfolio(await portRes.json());
      } catch (err) {
        console.error('Failed to load data:', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading) return <div className="p-6 text-center">Loading Trading Radar System...</div>;
  if (!data) return <div className="p-6 text-red-500 text-center">No Battle Plan found. Run morning_battle_plan.py first.</div>;

  const regimeLabel = data.market_regime?.regime || 'UNKNOWN';
  const recommendation = data.market_regime?.recommendation || { primary: 'CASH', risk_multiplier: 0, rationale: 'Waiting for analysis...' };
  
  const regimeColor = regimeLabel === 'BULLISH_TRENDING' ? '#10b981' : 
                      regimeLabel === 'SIDEWAYS_CHOPPY' ? '#f59e0b' : '#ef4444';

  const getTradingViewUrl = (symbol: string) => {
    const cleanSymbol = symbol.split('.')[0];
    return `https://www.tradingview.com/chart/?symbol=NSE:${cleanSymbol}`;
  };

  const getSetupColor = (setup: string) => {
    switch(setup) {
      case 'FUND_MOMENTUM': return { bg: 'rgba(168, 85, 247, 0.1)', text: '#a855f7' }; // Purple
      case 'QULLAMAGGIE': return { bg: 'rgba(16, 185, 129, 0.1)', text: '#10b981' };   // Green
      case 'EPISODIC_PIVOT': return { bg: 'rgba(236, 72, 153, 0.1)', text: '#ec4899' }; // Pink
      case 'REVERSION_BUY': return { bg: 'rgba(59, 130, 246, 0.1)', text: '#3b82f6' };  // Blue
      case 'REVERSION_SELL': return { bg: 'rgba(239, 68, 68, 0.1)', text: '#ef4444' }; // Red
      default: return { bg: 'rgba(107, 114, 128, 0.1)', text: '#6b7280' };             // Gray
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6" style={{ backgroundColor: 'var(--color-bg)', color: 'var(--color-text)' }}>
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex justify-between items-end border-b pb-4" style={{ borderColor: 'var(--color-border)' }}>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Radar size={28} style={{ color: 'var(--color-accent)' }} />
              <h1 className="text-2xl font-bold tracking-tight">Trading Radar</h1>
            </div>
            <p className="text-sm opacity-60">High-Octane NSE Momentum & Reversion Framework</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] uppercase font-bold opacity-40 tracking-widest">Analysis Time</p>
            <p className="text-sm font-mono">{new Date(data.timestamp).toLocaleString()}</p>
          </div>
        </div>

        {/* Top Cards: Regime & Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Regime Card */}
          <div className="p-6 rounded-xl border-2 flex flex-col justify-between" style={{ borderColor: regimeColor, backgroundColor: `${regimeColor}08` }}>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-2 block">Market State</span>
              <h2 className="text-3xl font-black mb-2 tracking-tighter" style={{ color: regimeColor }}>{regimeLabel.replace('_', ' ')}</h2>
              <p className="text-sm leading-snug opacity-80">{recommendation.rationale}</p>
            </div>
          </div>

          {/* Net Daily P&L Card */}
          <div className="p-6 rounded-xl border flex flex-col justify-between" style={{ borderColor: 'var(--color-border)', backgroundColor: (portfolio?.stats.net_pnl_currency || 0) >= 0 ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)' }}>
            <div>
              <span className="text-[10px] font-bold uppercase tracking-widest opacity-40 mb-2 block">Total Portfolio P&L</span>
              <div className="flex items-center gap-2 mb-2">
                <IndianRupee size={24} className={(portfolio?.stats.net_pnl_currency || 0) >= 0 ? 'text-green-500' : 'text-red-500'} />
                <h2 className={`text-3xl font-black ${(portfolio?.stats.net_pnl_currency || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  {portfolio?.stats.net_pnl_currency?.toLocaleString('en-IN') || 0}
                </h2>
              </div>
              <p className="text-xs opacity-60 italic">Fixed ₹10,000 / position</p>
            </div>
          </div>

          {/* Portfolio Stats */}
          <div className="p-6 rounded-xl border grid grid-cols-2 gap-4" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg-secondary)' }}>
            <div className="bg-black/5 p-3 rounded">
              <p className="text-2xl font-bold">{portfolio?.stats.win_rate || 0}%</p>
              <p className="text-[10px] uppercase font-bold opacity-40">Overall WR</p>
            </div>
            <div className="bg-black/5 p-3 rounded">
              <p className={`text-2xl font-bold ${(portfolio?.stats.total_pnl_pct || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {portfolio?.stats.total_pnl_pct || 0}%
              </p>
              <p className="text-[10px] uppercase font-bold opacity-40">Total PnL %</p>
            </div>
            <div className="bg-black/5 p-3 rounded">
              <p className="text-2xl font-bold">{portfolio?.active_positions.length || 0}</p>
              <p className="text-[10px] uppercase font-bold opacity-40">Active</p>
            </div>
            <div className="bg-black/5 p-3 rounded">
              <p className="text-2xl font-bold">{portfolio?.stats.total_trades || 0}</p>
              <p className="text-[10px] uppercase font-bold opacity-40">Closed</p>
            </div>
          </div>
        </div>

        {/* 1. Live Virtual Portfolio Section */}
        {portfolio && portfolio.active_positions.length > 0 && (
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.03)' }}>
            <div className="p-4 border-b flex justify-between items-center" style={{ borderColor: '#10b981' }}>
              <h3 className="font-bold flex items-center gap-2 text-green-600">
                <Briefcase size={18} />
                Live Tracker: Active Positions
              </h3>
              <span className="text-[10px] font-mono opacity-60 italic text-green-700">Updating Hourly</span>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-green-500/10 text-[10px] uppercase font-bold text-green-800">
                <tr>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Entry</th>
                  <th className="p-3">Current</th>
                  <th className="p-3">PnL %</th>
                  <th className="p-3">PnL (₹)</th>
                  <th className="p-3">Stop Loss</th>
                  <th className="p-3">Target</th>
                  <th className="p-3">Strategy</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.active_positions.map((pos, i) => {
                  const currPnL = (pos.pnl_pct / 100) * 10000;
                  return (
                    <tr key={i} className="border-b border-green-500/10 hover:bg-green-500/5">
                      <td className="p-3 font-bold text-green-700">
                        <div className="flex items-center gap-2">
                          {pos.symbol}
                          <a href={getTradingViewUrl(pos.symbol)} target="_blank" rel="noopener noreferrer" className="opacity-30 hover:opacity-100">
                            <ExternalLink size={12} />
                          </a>
                        </div>
                      </td>
                      <td className="p-3 font-mono">₹{pos.entry_price}</td>
                      <td className="p-3 font-mono">₹{pos.current_price}</td>
                      <td className={`p-3 font-mono font-bold ${pos.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {pos.pnl_pct > 0 ? '+' : ''}{pos.pnl_pct}%
                      </td>
                      <td className={`p-3 font-mono font-bold ${currPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ₹{currPnL.toFixed(2)}
                      </td>
                      <td className="p-3 font-mono text-red-500 opacity-60">₹{pos.stop_loss}</td>
                      <td className="p-3 font-mono text-blue-500 opacity-60">₹{pos.target}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-[9px] font-bold uppercase tracking-tighter">
                            {pos.setup_type.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 2. Closed Trades / History Section */}
        {portfolio && portfolio.closed_positions.length > 0 && (
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg-secondary)' }}>
            <div className="p-4 border-b flex justify-between items-center" style={{ borderColor: 'var(--color-border)' }}>
              <h3 className="font-bold flex items-center gap-2">
                <History size={18} />
                Trade History: Closed Positions
              </h3>
            </div>
            <table className="w-full text-left text-xs">
              <thead className="bg-black/5 text-[10px] uppercase font-bold opacity-60">
                <tr>
                  <th className="p-3">Symbol</th>
                  <th className="p-3">Entry</th>
                  <th className="p-3">Exit</th>
                  <th className="p-3">PnL %</th>
                  <th className="p-3">PnL (₹)</th>
                  <th className="p-3">Outcome</th>
                  <th className="p-3">Strategy</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.closed_positions.map((pos, i) => {
                  const currPnL = (pos.pnl_pct / 100) * 10000;
                  return (
                    <tr key={i} className="border-b border-black/5 hover:bg-black/5">
                      <td className="p-3 font-bold">{pos.symbol}</td>
                      <td className="p-3 font-mono opacity-60">₹{pos.entry_price}</td>
                      <td className="p-3 font-mono">₹{pos.exit_price}</td>
                      <td className={`p-3 font-mono font-bold ${pos.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {pos.pnl_pct > 0 ? '+' : ''}{pos.pnl_pct}%
                      </td>
                      <td className={`p-3 font-mono font-bold ${currPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ₹{currPnL.toFixed(2)}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${pos.status === 'CLOSED_TARGET' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
                            {pos.status.replace('CLOSED_', '')}
                        </span>
                      </td>
                      <td className="p-3 opacity-60 text-[9px] uppercase font-bold">{pos.setup_type}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* 3. Today's Scanner Scans Section */}
        <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg-secondary)' }}>
          <div className="p-4 border-b flex justify-between items-center" style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-bg)' }}>
            <h3 className="font-bold flex items-center gap-2">
              <Crosshair size={18} style={{ color: 'var(--color-accent)' }} />
              High-Conviction Radar Setups
            </h3>
            <span className="text-[10px] opacity-50 font-mono">Potential Opportunities</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-black/5 text-[11px] uppercase font-bold opacity-60">
                  <th className="p-4">Symbol</th>
                  <th className="p-4">RS Rating</th>
                  <th className="p-4">Strategy</th>
                  <th className="p-4">Entry (LTP)</th>
                  <th className="p-4">Stop Loss</th>
                  <th className="p-4">Target (1:3)</th>
                  <th className="p-4">ADR %</th>
                </tr>
              </thead>
              <tbody>
                {(data.scanner_data || []).map((item, i) => (
                  <tr key={i} className="border-b hover:bg-black/5 transition-colors" style={{ borderColor: 'var(--color-border)', backgroundColor: item.is_setup ? 'rgba(16, 185, 129, 0.05)' : 'inherit' }}>
                    <td className="p-4 font-bold">
                      <div className="flex items-center gap-2">
                        <span style={{ color: 'var(--color-accent)' }}>{item.symbol}</span>
                        <a 
                          href={getTradingViewUrl(item.symbol)} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="opacity-20 hover:opacity-100 transition-opacity"
                        >
                          <ExternalLink size={14} />
                        </a>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full" style={{ width: `${item.rs_rating}%`, backgroundColor: 'var(--color-accent)' }}></div>
                        </div>
                        <span className="font-mono text-xs">{item.rs_rating}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex gap-1 flex-wrap">
                        {(item.all_setups || [item.setup_type]).map((s, j) => {
                          const style = getSetupColor(s);
                          return (
                            <span key={j} className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter" style={{ backgroundColor: style.bg, color: style.text }}>
                              {s.replace('_', ' ')}
                            </span>
                          );
                        })}
                      </div>
                    </td>
                    <td className="p-4 font-mono">₹{item.entry}</td>
                    <td className="p-4 font-mono text-red-500">₹{item.stop}</td>
                    <td className="p-4 font-mono text-green-500">₹{item.target}</td>
                    <td className="p-4 font-mono opacity-70 text-xs">{item.adr}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer info */}
        <div className="flex justify-between items-center opacity-40 text-[10px] px-2">
          <div className="flex gap-6">
            <div className="flex items-center gap-1"><ShieldCheck size={14} /> Dynamic Stop: 0.5x ADR</div>
            <div className="flex items-center gap-1"><Target size={14} /> RR Target: 1:3</div>
            <div className="flex items-center gap-1"><AlertTriangle size={14} /> HMM Verified: {regimeLabel}</div>
          </div>
          <div className="font-mono uppercase tracking-tighter">Proprietary Momentum Engine v2.0</div>
        </div>

      </div>
    </div>
  );
}
