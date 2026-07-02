import React, { useState, useEffect } from 'react';
import { Cpu, RefreshCw, FolderOpen, AlertCircle, CheckCircle2, Loader2, Play } from 'lucide-react';

interface ModelsData {
  router_model: string;
  planner_model: string;
  available_models: string[];
}

export const ModelsSettings: React.FC = () => {
  const [data, setData] = useState<ModelsData>({
    router_model: '',
    planner_model: '',
    available_models: [],
  });
  
  const [loading, setLoading] = useState(true);
  const [switchingRouter, setSwitchingRouter] = useState(false);
  const [switchingPlanner, setSwitchingPlanner] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const API_BASE = 'http://127.0.0.1:8000/api/models';

  const fetchModels = async () => {
    try {
      const res = await fetch(API_BASE);
      if (res.ok) {
        const body = await res.json();
        setData(body);
      } else {
        setMessage({ type: 'error', text: 'Failed to retrieve active model configurations.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Backend model manager is unreachable.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleSelectRouter = async (modelName: string) => {
    if (modelName === data.router_model) return;
    setSwitchingRouter(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/router`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName }),
      });
      const resData = await res.json();
      if (res.ok && resData.success) {
        setData(prev => ({ ...prev, router_model: modelName }));
        setMessage({ type: 'success', text: `✓ Router model updated to ${modelName}.` });
      } else {
        setMessage({ type: 'error', text: resData.detail || 'Failed to update Router model.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error communicating with the backend. Switch aborted.' });
    } finally {
      setSwitchingRouter(false);
    }
  };

  const handleSelectPlanner = async (modelName: string) => {
    if (modelName === data.planner_model) return;
    setSwitchingPlanner(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/planner`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: modelName }),
      });
      const resData = await res.json();
      if (res.ok && resData.success) {
        setData(prev => ({ ...prev, planner_model: modelName }));
        setMessage({ type: 'success', text: `✓ Planner model updated to ${modelName}.` });
      } else {
        setMessage({ type: 'error', text: resData.detail || 'Failed to update Planner model.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Error communicating with the backend. Switch aborted.' });
    } finally {
      setSwitchingPlanner(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setMessage(null);
    try {
      const res = await fetch(`${API_BASE}/refresh`, { method: 'POST' });
      if (res.ok) {
        const body = await res.json();
        setData(body);
        setMessage({ type: 'success', text: 'Discovered model list updated.' });
      } else {
        setMessage({ type: 'error', text: 'Failed to refresh model scanning.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to communicate with the scanner service.' });
    } finally {
      setRefreshing(false);
    }
  };

  const handleOpenFolder = async () => {
    try {
      const res = await fetch(`${API_BASE}/open`, { method: 'POST' });
      if (!res.ok) {
        setMessage({ type: 'error', text: 'Failed to launch file explorer.' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Backend open service is unreachable.' });
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-[#141d26]/40" />
        <span className="text-xs text-[#141d26]/60 font-semibold">Loading model manager...</span>
      </div>
    );
  }

  const isFolderEmpty = data.available_models.length === 0;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 border-b border-black/5 pb-4">
        <h2 className="custom-font-heading text-2xl font-extrabold text-[#141d26]">
          GGUF Model Selection
        </h2>
        <p className="text-xs text-[#141d26]/60">
          Choose which local GGUF model instances Aether uses for routing and sequence planning.
        </p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl border flex items-start gap-3 text-xs leading-relaxed ${
          message.type === 'success' 
            ? 'bg-emerald-50 border-emerald-200/60 text-emerald-800' 
            : 'bg-rose-50 border-rose-200/60 text-rose-800'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div>{message.text}</div>
        </div>
      )}

      {isFolderEmpty ? (
        <div className="bg-[#f6f4ed] border border-black/10 rounded-xl p-8 flex flex-col items-center text-center gap-3">
          <AlertCircle className="w-10 h-10 text-amber-600" />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-bold text-[#141d26]">No GGUF models found.</span>
            <span className="text-xs text-[#141d26]/60 max-w-md">
              Place GGUF models inside <code className="bg-black/5 px-1.5 py-0.5 rounded font-mono text-[11px]">aether/models/gguf/</code>, then click Refresh below.
            </span>
          </div>
          <div className="flex gap-3 mt-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 border border-black/10 rounded-lg text-xs font-semibold hover:bg-black/5 active:bg-black/10 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh Models
            </button>
            <button
              onClick={handleOpenFolder}
              className="flex items-center gap-2 px-4 py-2 bg-[#16202a] text-white rounded-lg text-xs font-semibold hover:bg-[#1c2a38] active:bg-[#101720] cursor-pointer"
            >
              <FolderOpen className="w-3.5 h-3.5" />
              Open Models Folder
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Router Model Selection Card */}
            <div className="bg-white border border-black/5 rounded-xl p-5 shadow-sm flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <div className="flex flex-col gap-0.5">
                  <h3 className="custom-font-heading text-sm font-bold text-[#141d26] flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#141d26]/60" />
                    Router Model
                  </h3>
                  <span className="text-[10px] text-[#141d26]/40">Responsible for query categorization and routing.</span>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 border border-emerald-100 rounded text-[10px] font-semibold text-emerald-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Running
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-[#141d26]/40">Select Model</label>
                <div className="relative">
                  <select
                    value={data.router_model}
                    onChange={(e) => handleSelectRouter(e.target.value)}
                    disabled={switchingRouter || switchingPlanner}
                    className="w-full text-xs font-semibold bg-[#f6f4ed] border border-black/10 rounded-lg p-2.5 outline-none cursor-pointer disabled:opacity-50 appearance-none pr-8 text-[#141d26]"
                  >
                    {data.available_models.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[#141d26]/40 text-xs">
                    ▼
                  </div>
                </div>
              </div>

              {switchingRouter && (
                <div className="flex items-center gap-2 text-[10px] font-bold text-amber-700 animate-pulse bg-amber-50/50 p-2 rounded-lg border border-amber-100">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Reloading router server with new GGUF...
                </div>
              )}
            </div>

            {/* Planner Model Selection Card */}
            <div className="bg-white border border-black/5 rounded-xl p-5 shadow-sm flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <div className="flex flex-col gap-0.5">
                  <h3 className="custom-font-heading text-sm font-bold text-[#141d26] flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#141d26]/60" />
                    Planner Model
                  </h3>
                  <span className="text-[10px] text-[#141d26]/40">Drafts structured JSON sequences for action plans.</span>
                </div>
                <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 border border-emerald-100 rounded text-[10px] font-semibold text-emerald-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Running
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-wider text-[#141d26]/40">Select Model</label>
                <div className="relative">
                  <select
                    value={data.planner_model}
                    onChange={(e) => handleSelectPlanner(e.target.value)}
                    disabled={switchingRouter || switchingPlanner}
                    className="w-full text-xs font-semibold bg-[#f6f4ed] border border-black/10 rounded-lg p-2.5 outline-none cursor-pointer disabled:opacity-50 appearance-none pr-8 text-[#141d26]"
                  >
                    {data.available_models.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[#141d26]/40 text-xs">
                    ▼
                  </div>
                </div>
              </div>

              {switchingPlanner && (
                <div className="flex items-center gap-2 text-[10px] font-bold text-amber-700 animate-pulse bg-amber-50/50 p-2 rounded-lg border border-amber-100">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Reloading planner server with new GGUF...
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-black/5 pt-6 flex justify-between items-center">
            <div className="flex flex-col gap-0.5 text-left">
              <span className="text-xs font-bold text-[#141d26]">Detected Models</span>
              <span className="text-[10px] text-[#141d26]/40">
                {data.available_models.length} GGUF model{data.available_models.length !== 1 ? 's' : ''} found in models directory
              </span>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={handleRefresh}
                disabled={refreshing || switchingRouter || switchingPlanner}
                className="flex items-center gap-2 px-3 py-2 border border-black/10 rounded-lg text-xs font-semibold hover:bg-black/5 active:bg-black/10 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh Models
              </button>
              <button
                onClick={handleOpenFolder}
                className="flex items-center gap-2 px-3 py-2 bg-[#16202a] text-white rounded-lg text-xs font-semibold hover:bg-[#1c2a38] active:bg-[#101720] cursor-pointer"
              >
                <FolderOpen className="w-3.5 h-3.5" />
                Open Models Folder
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
