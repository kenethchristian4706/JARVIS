import React from 'react';
import type { LLMStatus } from '../types/events';

interface StatusCardProps {
  llmStatus: LLMStatus;
}

export const StatusCard: React.FC<StatusCardProps> = ({ llmStatus }) => {
  const {
    router_running,
    planner_running,
    router_model,
    router_port
  } = llmStatus;

  const isRunning = router_running || planner_running;

  // Extract model name or default
  const modelName = router_model ? router_model.split(/[\\/]/).pop() || router_model : 'qwen2.5-3b-instruct-q2_k.gguf';

  return (
    <div className="bg-[#0f161c] border border-[#232d38] rounded-lg p-5 flex flex-col gap-4 text-left font-sans">
      {/* Active status */}
      <div className="flex items-center gap-2">
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${isRunning ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
        <span className="text-xs font-bold text-white tracking-wide">
          {isRunning ? 'Local LLM online' : 'Local LLM offline'}
        </span>
      </div>

      {/* Runtime */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[9px] font-bold text-white/40 tracking-wider uppercase font-mono">
          RUNTIME
        </span>
        <span className="text-xs text-white/90 font-mono">
          windows-x64
        </span>
      </div>

      {/* Model */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[9px] font-bold text-white/40 tracking-wider uppercase font-mono">
          MODEL
        </span>
        <span className="text-xs text-white/90 font-mono break-all leading-relaxed">
          {modelName}
        </span>
      </div>

      {/* Endpoint */}
      <div className="flex flex-col gap-0.5">
        <span className="text-[9px] font-bold text-white/40 tracking-wider uppercase font-mono">
          ENDPOINT
        </span>
        <span className="text-xs text-white/90 font-mono">
          127.0.0.1:{router_port || '12345'}
        </span>
      </div>
    </div>
  );
};
