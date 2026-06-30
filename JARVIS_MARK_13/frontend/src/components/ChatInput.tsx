import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Trash2, Mic, MicOff } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
  clearChat: () => void;
  messagesCount: number;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  disabled, 
  clearChat, 
  messagesCount 
}) => {
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  return (
    <div className="w-full flex flex-col gap-2 p-4 bg-[#f6f4ed] relative">
      {isRecording && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-rose-50 border border-rose-200 rounded-full px-4 py-1.5 text-xs text-rose-600 flex items-center gap-2 animate-bounce shadow-md">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          Voice input active. Tap mic again to stop.
        </div>
      )}

      <div className="flex flex-col max-w-4xl mx-auto w-full bg-white border border-black/10 rounded-2xl p-3 shadow-sm focus-within:border-black/20 focus-within:shadow-[0_2px_12px_rgba(0,0,0,0.02)] transition-all duration-200">
        {/* Input Text Box */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={isRecording ? "Listening to voice input..." : "Type a local command, or start the Local LLM for conversation"}
          rows={1}
          style={{ minHeight: '38px' }}
          className="w-full bg-transparent text-sm text-[#141d26] outline-none border-none resize-none overflow-y-auto leading-relaxed py-1.5 px-2 select-text placeholder-gray-400"
        />

        {/* Controls and Actions row */}
        <div className="flex items-center justify-between border-t border-gray-100 pt-2.5 px-1 mt-1 shrink-0 select-none">
          <div className="flex items-center gap-2">
            {/* Voice Microphone Control */}
            <button
              onClick={toggleRecording}
              disabled={disabled}
              className={`w-8 h-8 rounded-full border border-gray-200 bg-white flex items-center justify-center transition-all cursor-pointer ${
                isRecording
                  ? 'border-rose-400 bg-rose-50 text-rose-500 scale-105 animate-pulse'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
              }`}
              title="Toggle Voice Input Mode"
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            {/* Clear Chat Control */}
            <button
              onClick={clearChat}
              disabled={messagesCount === 0}
              className="w-8 h-8 rounded-full border border-gray-200 bg-white flex items-center justify-center text-gray-400 hover:text-rose-500 hover:bg-gray-50 transition-all cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed"
              title="Clear Chat Logs"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Send Action Hook */}
          <button
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer ${
              text.trim() && !disabled
                ? 'bg-gray-700 text-white hover:bg-gray-800 shadow-sm'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            title="Dispatch Task"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="max-w-4xl mx-auto w-full flex items-center justify-between text-[10px] text-[#141d26]/40 px-2 mt-0.5 select-none">
        <span>Press <kbd className="bg-black/5 px-1.5 py-0.5 rounded border border-black/5 font-mono text-[9px]">Enter</kbd> to Send, <kbd className="bg-black/5 px-1.5 py-0.5 rounded border border-black/5 font-mono text-[9px]">Shift+Enter</kbd> for new line</span>
        <span>Secure Offline Mode</span>
      </div>
    </div>
  );
};
