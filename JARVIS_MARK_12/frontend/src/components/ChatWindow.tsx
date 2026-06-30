import React, { useRef, useEffect } from 'react';
import type { Message, ConnectionStatus, LLMStatus } from '../types/events';
import { MessageBubble } from './MessageBubble';
import { Bot } from 'lucide-react';

interface ChatWindowProps {
  messages: Message[];
  connectionStatus: ConnectionStatus;
  llmStatus: LLMStatus;
  triggerLLM: (action: 'start_llm' | 'stop_llm') => void;
  clearChat: () => void;
  onQuickAction: (actionText: string) => void;
  onRespondToPrompt: (promptId: string, selection: string) => void;
  refreshStatus: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  connectionStatus,
  llmStatus,
  triggerLLM,
  onQuickAction,
  onRespondToPrompt,
  refreshStatus
}) => {

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const isServerRunning = llmStatus.router_running || llmStatus.planner_running;

  const quickActions = [
    { text: "Open Chrome", icon: "🌐" },
    { text: "Take a screenshot", icon: "📸" },
    { text: "Set volume to 50", icon: "🔊" },
    { text: "Create folder project on Desktop", icon: "📂" }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f6f4ed] overflow-hidden select-text text-[#141d26]">
      {/* 1. Main Header */}
      <header className="h-16 border-b border-black/5 bg-[#f6f4ed]/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 select-none">
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-bold text-emerald-700 tracking-wider uppercase font-sans">
            OFFLINE ASSISTANT
          </span>
          <h2 className="text-xl font-bold text-[#141d26] m-0 leading-tight">
            Conversation
          </h2>
        </div>

        {/* Action Hooks */}
        <div className="flex items-center gap-2">
          <button
            onClick={refreshStatus}
            disabled={connectionStatus === 'disconnected'}
            className="px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-black text-xs font-semibold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            title="Refresh Server Daemon Status"
          >
            Refresh
          </button>

          <button
            onClick={() => triggerLLM(isServerRunning ? 'stop_llm' : 'start_llm')}
            disabled={connectionStatus === 'disconnected'}
            className="px-4 py-2 bg-black hover:bg-black/90 text-white text-xs font-bold rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            title={isServerRunning ? "Terminate Local LLM processes" : "Boot Local LLM processes"}
          >
            {isServerRunning ? 'Stop Local LLM' : 'Start Local LLM'}
          </button>
        </div>
      </header>

      {/* 2. Chat Log Scroll Feed */}
      <div 
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4 select-text"
      >
        {messages.length === 0 ? (
          /* Welcome panel */
          <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto w-full text-center gap-8 py-10 select-none">
            <div className="w-full bg-white border border-black/5 rounded-2xl shadow-sm p-8 flex flex-col items-center gap-6">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#ecc870] to-[#24C8DB] p-0.5 shadow-md">
                <div className="w-full h-full bg-[#141d26] rounded-[14px] flex items-center justify-center">
                  <Bot className="w-7 h-7 text-[#24C8DB]" />
                </div>
              </div>
              
              <div className="flex flex-col gap-2">
                <h3 className="text-xl font-bold text-[#141d26] tracking-tight">
                  Tell Aether what to do.
                </h3>
                <p className="text-xs text-[#141d26]/60 max-w-md leading-relaxed">
                  Chat normally, open your mail app, draft an email, or send the visible mail draft where supported. You can also find and open local files here.
                </p>
              </div>
            </div>

            {/* Quick Action Suggestion Tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
              {quickActions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => onQuickAction(action.text)}
                  className="bg-white border border-black/5 rounded-xl p-4 text-left flex items-start gap-3 hover:bg-gray-50/50 shadow-sm transition-all duration-200 cursor-pointer hover:scale-[1.005]"
                >
                  <span className="text-lg shrink-0 mt-0.5">{action.icon}</span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-xs font-semibold text-[#141d26] leading-tight">
                      {action.text}
                    </span>
                    <span className="text-[10px] text-[#141d26]/40 font-mono">
                      Execute task
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Render messages */
          <div className="max-w-4xl mx-auto w-full flex flex-col gap-3 py-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} onRespondToPrompt={onRespondToPrompt} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
