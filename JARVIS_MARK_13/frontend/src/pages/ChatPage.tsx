import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from '../components/Sidebar';
import { ChatWindow } from '../components/ChatWindow';
import { ChatInput } from '../components/ChatInput';
import { useWebSocket } from '../hooks/useWebSocket';
import { Sliders, Cpu, Activity, ShieldCheck, Mail, Settings, Info } from 'lucide-react';
import { EmailSettings } from '../components/EmailSettings';
import { ModelsSettings } from '../components/ModelsSettings';

export const ChatPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'settings'>('chat');
  const [settingsTab, setSettingsTab] = useState<'general' | 'models' | 'email' | 'about'>('general');
  const lastQueryRef = useRef<string | null>(null);

  const {
    messages,
    connectionStatus,
    llmStatus,
    sendMessage,
    respondToPrompt,
    triggerLLMServer,
    refreshLLMStatus,
    clearChat
  } = useWebSocket();

  const [showClearedMessage, setShowClearedMessage] = useState(false);

  // Auto-switch to email settings if an email tool requires connection/login
  useEffect(() => {
    const lastMsg = messages[messages.length - 1];
    if (
      lastMsg &&
      lastMsg.sender === 'assistant' &&
      lastMsg.status === 'error' &&
      (lastMsg.errorCode === 'EMAIL_NOT_CONNECTED' || lastMsg.errorMessage?.includes('EMAIL_NOT_CONNECTED'))
    ) {
      setActiveTab('settings');
      setSettingsTab('email');
    }
  }, [messages]);

  const handleSendMessage = (text: string) => {
    lastQueryRef.current = text;
    sendMessage(text);
  };

  const handleClearChat = () => {
    clearChat();
    setShowClearedMessage(true);
    setTimeout(() => {
      setShowClearedMessage(false);
    }, 3000);
  };

  const handleQuickAction = (text: string) => {
    handleSendMessage(text);
  };

  const handleConnectSuccess = () => {
    if (lastQueryRef.current) {
      const query = lastQueryRef.current;
      setTimeout(() => {
        setActiveTab('chat');
        handleSendMessage(query);
      }, 1000);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f6f4ed]">
      {/* Navigation left pane */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        llmStatus={llmStatus}
        triggerLLM={triggerLLMServer}
        refreshStatus={refreshLLMStatus}
        connectionStatus={connectionStatus}
        showClearedMessage={showClearedMessage}
      />

      {/* Main dashboard content view */}
      <main className="flex-1 flex flex-col h-full overflow-hidden border-l border-black/5 relative bg-[#f6f4ed]">
        {activeTab === 'chat' ? (
          <React.Fragment>
            <ChatWindow
              messages={messages}
              connectionStatus={connectionStatus}
              llmStatus={llmStatus}
              triggerLLM={triggerLLMServer}
              clearChat={handleClearChat}
              onQuickAction={handleQuickAction}
              onRespondToPrompt={respondToPrompt}
              refreshStatus={refreshLLMStatus}
            />
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={connectionStatus === 'disconnected'}
              clearChat={handleClearChat}
              messagesCount={messages.length}
            />
          </React.Fragment>
        ) : (
          /* Settings Tab Content View with sub-navigation */
          <div className="flex-1 flex overflow-hidden">
            {/* Settings Sub-navigation Sidebar */}
            <div className="w-64 border-r border-black/5 bg-white/30 flex flex-col p-6 gap-1 shrink-0 select-none text-left">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#141d26]/40 px-3 mb-2">Category Settings</span>
              
              <button
                onClick={() => setSettingsTab('general')}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  settingsTab === 'general' ? 'bg-[#16202a] text-white shadow-sm' : 'text-[#141d26]/70 hover:bg-black/5'
                }`}
              >
                <Settings className="w-4 h-4" />
                General
              </button>

              <button
                onClick={() => setSettingsTab('models')}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  settingsTab === 'models' ? 'bg-[#16202a] text-white shadow-sm' : 'text-[#141d26]/70 hover:bg-black/5'
                }`}
              >
                <Cpu className="w-4 h-4" />
                Models
              </button>

              <button
                onClick={() => setSettingsTab('email')}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  settingsTab === 'email' ? 'bg-[#16202a] text-white shadow-sm' : 'text-[#141d26]/70 hover:bg-black/5'
                }`}
              >
                <Mail className="w-4 h-4" />
                Email
              </button>

              <button
                onClick={() => setSettingsTab('about')}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all duration-150 cursor-pointer ${
                  settingsTab === 'about' ? 'bg-[#16202a] text-white shadow-sm' : 'text-[#141d26]/70 hover:bg-black/5'
                }`}
              >
                <Info className="w-4 h-4" />
                About
              </button>
            </div>

            {/* Sub-tab Content Pane */}
            <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 text-left max-w-4xl mx-auto w-full select-text text-[#141d26]">
              {settingsTab === 'general' && (
                <>
                  <div className="flex flex-col gap-1 border-b border-black/5 pb-4">
                    <h2 className="custom-font-heading text-2xl font-extrabold text-[#141d26]">
                      General Configuration
                    </h2>
                    <p className="text-xs text-[#141d26]/60">
                      Configure local LLM model instances, endpoints, and sidecar network ports.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white border border-black/5 rounded-xl p-5 shadow-sm flex flex-col gap-3">
                      <h3 className="custom-font-heading text-sm font-bold text-[#141d26] flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-[#141d26]/60" />
                        Router Configuration (3B)
                      </h3>
                      <div className="flex flex-col gap-2 text-xs text-[#141d26]/80 leading-relaxed font-mono">
                        <div className="flex justify-between border-b border-black/5 pb-1.5">
                          <span className="text-[#141d26]/40">LLM Endpoint:</span>
                          <span>{llmStatus.endpoint}:{llmStatus.router_port}</span>
                        </div>
                        <div className="flex justify-between border-b border-black/5 pb-1.5">
                          <span className="text-[#141d26]/40">GGUF Filename:</span>
                          <span className="break-all">{llmStatus.router_model}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#141d26]/40">Temperature:</span>
                          <span>0.0 (Deterministic)</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white border border-black/5 rounded-xl p-5 shadow-sm flex flex-col gap-3">
                      <h3 className="custom-font-heading text-sm font-bold text-[#141d26] flex items-center gap-2">
                        <Activity className="w-4 h-4 text-[#141d26]/60" />
                        Planner Configuration (7B)
                      </h3>
                      <div className="flex flex-col gap-2 text-xs text-[#141d26]/80 leading-relaxed font-mono">
                        <div className="flex justify-between border-b border-black/5 pb-1.5">
                          <span className="text-[#141d26]/40">LLM Endpoint:</span>
                          <span>{llmStatus.endpoint}:{llmStatus.planner_port}</span>
                        </div>
                        <div className="flex justify-between border-b border-black/5 pb-1.5">
                          <span className="text-[#141d26]/40">GGUF Filename:</span>
                          <span className="break-all">{llmStatus.planner_model}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-[#141d26]/40">Temperature:</span>
                          <span>0.0 (Deterministic)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}

              {settingsTab === 'models' && (
                <ModelsSettings />
              )}



              {settingsTab === 'email' && (
                <EmailSettings onConnectSuccess={handleConnectSuccess} />
              )}

              {settingsTab === 'about' && (
                <>
                  <div className="flex flex-col gap-1 border-b border-black/5 pb-4">
                    <h2 className="custom-font-heading text-2xl font-extrabold text-[#141d26]">
                      About Aether
                    </h2>
                    <p className="text-xs text-[#141d26]/60">
                      Version information, cognitive pipeline architecture summary, and privacy assurances.
                    </p>
                  </div>
                  
                  {/* Architecture Pipeline Explanation */}
                  <div className="bg-white border border-black/5 rounded-xl p-5 shadow-sm flex flex-col gap-4">
                    <h3 className="custom-font-heading text-sm font-bold text-[#141d26] flex items-center gap-2 border-b border-black/5 pb-2">
                      <Sliders className="w-4 h-4 text-[#141d26]/60" />
                      Aether Cognitive Pipeline Architecture
                    </h3>

                    <div className="flex flex-col gap-4 text-xs text-[#141d26]/80 leading-relaxed">
                      <div className="flex gap-3">
                        <div className="w-7 h-7 rounded bg-black/5 flex items-center justify-center shrink-0 font-bold text-[#141d26] border border-black/5">1</div>
                        <div>
                          <strong className="text-[#141d26]">Query Normalization & Routing:</strong> The input string is processed via a local Qwen 3B Router to determine categories (Apps, Files, Browser, System, or Email).
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-7 h-7 rounded bg-black/5 flex items-center justify-center shrink-0 font-bold text-[#141d26] border border-black/5">2</div>
                        <div>
                          <strong className="text-[#141d26]">Candidate Tool Expansion:</strong> A Python category filter maps the user's intent to candidate tools to trim context length, preventing model hallucinations.
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-7 h-7 rounded bg-black/5 flex items-center justify-center shrink-0 font-bold text-[#141d26] border border-black/5">3</div>
                        <div>
                          <strong className="text-[#141d26]">Structured Action Planning:</strong> The query, context details, and tool metadata are processed by Qwen 7B Coder constrained by a dynamic JSON Schema to draft the sequential plan.
                        </div>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-7 h-7 rounded bg-black/5 flex items-center justify-center shrink-0 font-bold text-[#141d26] border border-black/5">4</div>
                        <div>
                          <strong className="text-[#141d26]">Rule Validation & Execution:</strong> The generated actions pass through a validator checking for safety regulations and parameters structure compatibility, then execute locally.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-emerald-50 border border-emerald-200/60 rounded-xl p-4 flex items-start gap-3">
                    <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div className="text-xs text-emerald-800 leading-relaxed">
                      <span className="font-bold block mb-0.5 text-emerald-950">Full Privacy Assurance</span>
                      Aether runs completely offline on your desktop. No queries, files content, clipboard logs, or task descriptions are forwarded to external networks. All computations run locally.
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default ChatPage;
