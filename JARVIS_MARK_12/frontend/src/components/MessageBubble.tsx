import React from 'react';
import type { Message } from '../types/events';
import { User, Bot } from 'lucide-react';
import { ToolEventCard } from './ToolEventCard';

interface MessageBubbleProps {
  message: Message;
  onRespondToPrompt?: (promptId: string, selection: string) => void;
}

const renderInlineStyles = (line: string) => {
  const parts = line.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index} className="font-bold text-[#141d26]">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index} className="bg-black/5 border border-black/5 rounded px-1.5 py-0.5 text-xs font-mono text-amber-700">{part.slice(1, -1)}</code>;
    }
    return part;
  });
};

const renderFormattedText = (text: string) => {
  if (!text) return null;
  
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, index) => {
    if (part.startsWith('```')) {
      const match = part.match(/```(\w*)\n([\s\S]*?)```/);
      const language = match ? match[1] : '';
      const code = match ? match[2] : part.slice(3, -3);
      return (
        <pre key={index} className="bg-[#1a232d] rounded-lg p-3 my-2 border border-black/10 font-mono text-xs text-white/95 overflow-x-auto select-text leading-relaxed text-left">
          {language && <div className="text-[10px] text-white/30 uppercase tracking-widest mb-1.5 border-b border-white/5 pb-1 font-sans font-bold">{language}</div>}
          <code>{code.trim()}</code>
        </pre>
      );
    }
    
    return (
      <div key={index} className="whitespace-pre-wrap select-text leading-relaxed text-sm text-[#141d26]/85">
        {part.split('\n').map((line, lIdx) => {
          if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
            return (
              <li key={lIdx} className="ml-4 list-disc pl-1 text-[#141d26]/85 py-0.5">
                {renderInlineStyles(line.trim().substring(2))}
              </li>
            );
          }
          if (line.startsWith('### ')) {
            return <h4 key={lIdx} className="text-sm font-bold text-[#141d26] mt-3 mb-1">{renderInlineStyles(line.substring(4))}</h4>;
          }
          if (line.startsWith('## ')) {
            return <h3 key={lIdx} className="text-base font-bold text-emerald-800 mt-4 mb-2">{renderInlineStyles(line.substring(3))}</h3>;
          }
          if (line.startsWith('# ')) {
            return <h2 key={lIdx} className="text-lg font-bold text-[#141d26] mt-5 mb-3">{renderInlineStyles(line.substring(2))}</h2>;
          }
          
          return <p key={lIdx} className="my-1.5 min-h-[1px]">{renderInlineStyles(line)}</p>;
        })}
      </div>
    );
  });
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, onRespondToPrompt }) => {
  const isUser = message.sender === 'user';

  return (
    <div className={`w-full flex gap-4 ${isUser ? 'justify-end' : 'justify-start'} py-2`}>
      {/* Bot Avatar Icon (Left side) */}
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-[#141d26] flex items-center justify-center shrink-0 shadow-sm border border-black/5">
          <Bot className="w-4 h-4 text-[#ecc870]" />
        </div>
      )}

      {/* Message Box */}
      <div className={`flex flex-col gap-1.5 max-w-2xl text-left ${isUser ? 'items-end' : 'items-start'}`}>
        <div className="flex items-center gap-2 text-[10px] text-[#141d26]/40 font-semibold px-1 select-none">
          <span>{isUser ? 'You' : 'Aether'}</span>
          <span>•</span>
          <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>

        <div className={`rounded-xl px-4 py-3 border border-black/5 bg-white text-[#141d26] shadow-sm transition-all duration-300`}>
          {/* Main output text */}
          {message.text ? (
            <div className="max-w-none text-left">
              {renderFormattedText(message.text)}
            </div>
          ) : (
            !isUser && !message.thinkingMessage && !message.errorMessage && (
              <span className="text-xs text-[#141d26]/40 italic">Processing pipeline...</span>
            )
          )}

          {/* Embedded live planner tool status metrics */}
          {!isUser && (
            <div className="mt-2.5">
              <ToolEventCard
                plan={message.plan}
                currentStepIndex={message.currentStepIndex}
                stepsStatus={message.stepsStatus}
                toolEvents={message.toolEvents}
                thinkingMessage={message.status === 'success' || message.status === 'error' || message.text ? undefined : message.thinkingMessage}
                errorMessage={message.errorMessage}
                activePrompt={message.activePrompt}
                promptAnswer={message.promptAnswer}
                onRespond={onRespondToPrompt}
              />
            </div>
          )}
        </div>
      </div>

      {/* User Avatar Icon (Right side) */}
      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-white border border-black/10 flex items-center justify-center shrink-0 shadow-sm">
          <User className="w-4 h-4 text-[#141d26]/75" />
        </div>
      )}
    </div>
  );
};
