import React, { useState } from 'react';
import {
  AppWindow,
  FolderOpen,
  Globe,
  Mail,
  Sliders,
  CheckCircle2,
  XCircle,
  Loader2,
  ListTodo,
  AlertCircle,
  HelpCircle
} from 'lucide-react';

interface ToolEventCardProps {
  plan?: string[];
  currentStepIndex?: number;
  stepsStatus?: { [stepDescription: string]: 'pending' | 'running' | 'success' | 'error' };
  toolEvents?: { tool: string; success?: boolean; running?: boolean }[];
  thinkingMessage?: string;
  errorMessage?: string;
  activePrompt?: { prompt_id: string; title: string; options: string[] };
  promptAnswer?: string;
  onRespond?: (promptId: string, selection: string) => void;
}

const getToolIcon = (toolName: string) => {
  const t = toolName.toLowerCase();
  if (t.includes('app')) {
    return <AppWindow className="w-4 h-4 text-amber-600" />;
  }
  if (
    t.includes('file') || 
    t.includes('dir') || 
    t.includes('folder') || 
    t.includes('archive') || 
    t.includes('compress') || 
    t.includes('read') || 
    t.includes('append') || 
    t.includes('rename') || 
    t.includes('delete') || 
    t.includes('copy') || 
    t.includes('move') || 
    t.includes('info')
  ) {
    return <FolderOpen className="w-4 h-4 text-[#24C8DB]" />;
  }
  if (
    t.includes('web') || 
    t.includes('url') || 
    t.includes('browser') || 
    t.includes('tab') || 
    t.includes('youtube') || 
    t.includes('download')
  ) {
    return <Globe className="w-4 h-4 text-sky-600" />;
  }
  if (t.includes('email')) {
    return <Mail className="w-4 h-4 text-emerald-600" />;
  }
  return <Sliders className="w-4 h-4 text-purple-600" />;
};

const PromptWriteIn: React.FC<{ 
  promptId: string; 
  onRespond: (promptId: string, selection: string) => void;
  hasOptions: boolean;
}> = ({ promptId, onRespond, hasOptions }) => {
  const [inputValue, setInputValue] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    onRespond(promptId, inputValue.trim());
    setInputValue('');
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-center w-full">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder={hasOptions ? "Or type a custom path/selection here..." : "Type response here..."}
        className="flex-1 bg-gray-50 border border-black/10 rounded-lg px-3 py-2 text-xs text-[#141d26] outline-none focus:border-black/30 font-sans"
      />
      <button
        type="submit"
        disabled={!inputValue.trim()}
        className="px-4 py-2 rounded-lg bg-black hover:bg-black/90 disabled:bg-gray-100 text-white disabled:text-gray-400 text-xs font-bold transition-all shrink-0 cursor-pointer disabled:cursor-not-allowed select-none"
      >
        Submit
      </button>
      <button
        type="button"
        onClick={() => onRespond(promptId, 'cancel')}
        className="px-3 py-2 rounded-lg bg-gray-100 hover:bg-rose-50 border border-transparent text-gray-500 hover:text-rose-600 text-xs font-bold transition-all shrink-0 cursor-pointer select-none"
      >
        Cancel
      </button>
    </form>
  );
};

export const ToolEventCard: React.FC<ToolEventCardProps> = ({
  plan,
  stepsStatus = {},
  toolEvents = [],
  thinkingMessage,
  errorMessage,
  activePrompt,
  promptAnswer,
  onRespond
}) => {
  const hasPlan = plan && plan.length > 0;
  const hasTools = toolEvents && toolEvents.length > 0;

  return (
    <div className="w-full max-w-2xl bg-gray-50 border border-black/5 rounded-xl p-4 flex flex-col gap-4 text-left shadow-sm">
      {/* 1. Live Thinking State */}
      {thinkingMessage && (
        <div className="flex items-center gap-3 text-xs text-emerald-800 font-medium">
          <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
          <span>{thinkingMessage}</span>
          <span className="flex-1 h-[1px] bg-emerald-200 rounded-full overflow-hidden relative">
            <span className="absolute top-0 left-0 bottom-0 w-1/3 bg-gradient-to-r from-[#ecc870] to-[#24C8DB] rounded-full animate-[loading_1.5s_infinite]" />
          </span>
        </div>
      )}

      {/* 2. Visual Plan List */}
      {hasPlan && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2 border-b border-black/5 pb-1.5">
            <ListTodo className="w-4 h-4 text-amber-600" />
            <h4 className="text-xs font-bold text-[#141d26]/60 uppercase tracking-wider">
              Execution Plan
            </h4>
          </div>

          <div className="flex flex-col gap-2.5 pl-1.5 relative border-l border-black/5 ml-2.5">
            {plan.map((step, idx) => {
              const status = stepsStatus[step] || 'pending';
              let icon = <span className="w-2 h-2 rounded-full bg-black/15" />;
              let textColor = 'text-[#141d26]/40';
              let borderHighlight = '-ml-[7px]';

              if (status === 'success') {
                icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 bg-white rounded-full shrink-0" />;
                textColor = 'text-[#141d26]/50 line-through decoration-[#141d26]/20';
                borderHighlight = '-ml-[10px] bg-emerald-50';
              } else if (status === 'running') {
                icon = <Loader2 className="w-3.5 h-3.5 text-emerald-600 bg-white rounded-full shrink-0 animate-spin" />;
                textColor = 'text-emerald-800 font-semibold';
                borderHighlight = '-ml-[10px] bg-emerald-50 ring-4 ring-emerald-500/5';
              } else if (status === 'error') {
                icon = <XCircle className="w-3.5 h-3.5 text-rose-600 bg-white rounded-full shrink-0" />;
                textColor = 'text-rose-600 font-medium';
                borderHighlight = '-ml-[10px] bg-rose-50';
              }

              return (
                <div key={idx} className="flex items-start gap-3 relative py-0.5">
                  <div className={`z-10 flex items-center justify-center rounded-full transition-all shrink-0 ${borderHighlight}`}>
                    {icon}
                  </div>
                  <span className={`text-xs select-text ${textColor}`}>
                    {idx + 1}. {step}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 3. Active User Prompt Card */}
      {activePrompt && onRespond && (
        <div className="bg-white border border-[#24C8DB]/30 rounded-xl p-4 flex flex-col gap-3.5 shadow-sm relative overflow-hidden text-[#141d26]">
          <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-[#24C8DB]" />
          
          <div className="flex items-center gap-2 border-b border-black/5 pb-2 text-[#24C8DB] pl-1.5">
            <HelpCircle className="w-4 h-4" />
            <span className="font-bold text-xs uppercase tracking-wider">
              User Input Needed
            </span>
          </div>
          
          <div className="text-xs text-[#141d26] leading-relaxed whitespace-pre-wrap font-medium select-text pl-1.5">
            {activePrompt.title}
          </div>
          
          {activePrompt.options.length > 0 && (
            <div className="flex flex-col gap-2 pl-1.5">
              {activePrompt.options.map((opt, idx) => (
                <button
                  key={idx}
                  onClick={() => onRespond(activePrompt.prompt_id, String(idx + 1))}
                  className="w-full text-left bg-gray-50 hover:bg-gray-100 border border-black/5 rounded-lg px-3 py-2 text-xs text-[#141d26]/80 hover:text-black transition-all cursor-pointer font-medium select-none"
                >
                  <span className="text-amber-600 font-bold mr-1.5">{idx + 1}.</span>
                  {opt}
                </button>
              ))}
            </div>
          )}
          
          <div className="pl-1.5 mt-1">
            <PromptWriteIn 
              promptId={activePrompt.prompt_id} 
              onRespond={onRespond} 
              hasOptions={activePrompt.options.length > 0}
            />
          </div>
        </div>
      )}

      {/* 4. Completed Prompt Answer Log */}
      {promptAnswer && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-3.5 flex items-start gap-3 text-emerald-800 text-xs">
          <CheckCircle2 className="w-4.5 h-4.5 shrink-0 mt-0.5 text-emerald-600" />
          <div className="flex flex-col gap-0.5 select-text text-left">
            <span className="font-bold text-[#141d26]/40 text-[9px] uppercase tracking-widest">
              Submitted Input
            </span>
            <span className="font-medium text-emerald-950 leading-relaxed">
              Selected: {promptAnswer}
            </span>
          </div>
        </div>
      )}

      {/* 5. Live Sub-tool Execution Badges */}
      {hasTools && (
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            {toolEvents.map((t, idx) => (
              <div
                key={idx}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs border transition-all ${
                  t.running
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800 animate-pulse'
                    : t.success
                    ? 'bg-emerald-50 border-emerald-150 text-emerald-800'
                    : 'bg-rose-50 border-rose-150 text-rose-800'
                }`}
              >
                {getToolIcon(t.tool)}
                <span className="font-mono text-[11px] font-medium">{t.tool}</span>
                <span className="text-[10px] opacity-75 font-semibold">
                  {t.running ? '⏳ Running...' : t.success ? '✅ Success' : '❌ Failed'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Error Message Card */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 flex items-start gap-2.5 text-rose-800 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1 select-text">
            <span className="font-bold">Execution Interrupted</span>
            <span className="leading-relaxed opacity-90">{errorMessage}</span>
          </div>
        </div>
      )}
    </div>
  );
};

