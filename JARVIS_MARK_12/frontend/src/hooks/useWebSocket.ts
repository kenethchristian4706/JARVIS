import { useEffect, useState, useRef, useCallback } from 'react';
import type { ConnectionStatus, LLMStatus, Message, PipelineEvent } from '../types/events';
import { defaultWsService } from '../services/websocket';

export function useWebSocket() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [llmStatus, setLlmStatus] = useState<LLMStatus>({
    router_running: false,
    planner_running: false,
    router_model: 'qwen2.5-3b-instruct-q4_k_m.gguf',
    planner_model: 'qwen2.5-coder-7b-instruct-q4_k_m.gguf',
    router_port: 12345,
    planner_port: 12346,
    endpoint: 'http://127.0.0.1'
  });

  const messageIdRef = useRef<string | null>(null);

  const handleEvent = useCallback((event: PipelineEvent) => {
    if (event.type === 'llm_status') {
      setLlmStatus({
        router_running: event.router_running,
        planner_running: event.planner_running,
        router_model: event.router_model,
        planner_model: event.planner_model,
        router_port: event.router_port,
        planner_port: event.planner_port,
        endpoint: event.endpoint
      });
      return;
    }

    setMessages((prevMessages) => {
      let activeId = messageIdRef.current;
      let assistantMsgIndex = prevMessages.findIndex((m) => m.id === activeId);

      if (!activeId || assistantMsgIndex === -1) {
        const newId = 'assistant-' + Date.now();
        messageIdRef.current = newId;
        const newAssistantMsg: Message = {
          id: newId,
          sender: 'assistant',
          text: '',
          timestamp: new Date(),
          status: 'pending',
          toolEvents: [],
          stepsStatus: {}
        };
        prevMessages = [...prevMessages, newAssistantMsg];
        assistantMsgIndex = prevMessages.length - 1;
      }

      const assistantMsg = { ...prevMessages[assistantMsgIndex] };
      const updatedMessages = [...prevMessages];

      // Deep copy nested objects for react re-renders
      assistantMsg.stepsStatus = assistantMsg.stepsStatus ? { ...assistantMsg.stepsStatus } : {};
      assistantMsg.toolEvents = assistantMsg.toolEvents ? [...assistantMsg.toolEvents] : [];

      switch (event.type) {
        case 'thinking':
          assistantMsg.thinkingMessage = event.message;
          break;

        case 'plan':
          assistantMsg.plan = event.steps;
          assistantMsg.stepsStatus = {};
          event.steps.forEach((step) => {
            if (assistantMsg.stepsStatus) {
              assistantMsg.stepsStatus[step] = 'pending';
            }
          });
          assistantMsg.currentStepIndex = 0;
          break;

        case 'step_start':
          if (assistantMsg.stepsStatus) {
            assistantMsg.stepsStatus[event.step] = 'running';
          }
          break;

        case 'step_complete':
          if (assistantMsg.stepsStatus) {
            assistantMsg.stepsStatus[event.step] = event.success ? 'success' : 'error';
          }
          if (assistantMsg.currentStepIndex !== undefined && assistantMsg.plan) {
            const stepIdx = assistantMsg.plan.indexOf(event.step);
            if (stepIdx !== -1) {
              assistantMsg.currentStepIndex = Math.max(assistantMsg.currentStepIndex, stepIdx + 1);
            }
          }
          break;

        case 'tool_start':
          if (!assistantMsg.toolEvents.some(t => t.tool === event.tool && t.running)) {
            assistantMsg.toolEvents.push({ tool: event.tool, running: true });
          }
          break;

        case 'tool_complete':
          assistantMsg.toolEvents = assistantMsg.toolEvents.map((t) =>
            t.tool === event.tool ? { ...t, running: false, success: event.success } : t
          );
          break;

        case 'user_prompt':
          assistantMsg.activePrompt = {
            prompt_id: event.prompt_id,
            title: event.title,
            options: event.options
          };
          assistantMsg.thinkingMessage = undefined; // Hide default loading state during prompt
          break;

        case 'error':
          assistantMsg.errorMessage = event.message;
          assistantMsg.errorCode = event.error_code;
          assistantMsg.status = 'error';
          assistantMsg.thinkingMessage = undefined;
          assistantMsg.activePrompt = undefined;
          messageIdRef.current = null; 
          break;

        case 'final_response':
          assistantMsg.text = event.message;
          assistantMsg.status = 'success';
          assistantMsg.thinkingMessage = undefined;
          assistantMsg.activePrompt = undefined;
          messageIdRef.current = null; 
          break;
      }

      updatedMessages[assistantMsgIndex] = assistantMsg;
      return updatedMessages;
    });
  }, []);

  const handleConnectionChange = useCallback((connected: boolean) => {
    setConnectionStatus(connected ? 'connected' : 'disconnected');
  }, []);

  useEffect(() => {
    defaultWsService.connect(handleEvent, handleConnectionChange);
    return () => {
      defaultWsService.disconnect();
    };
  }, [handleEvent, handleConnectionChange]);

  const sendMessage = useCallback((text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: 'user-' + Date.now(),
      sender: 'user',
      text: text,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMsg]);
    messageIdRef.current = null;

    defaultWsService.sendMessage(text);
  }, []);

  const respondToPrompt = useCallback((promptId: string, selection: string) => {
    // Send response over WS
    defaultWsService.sendPromptResponse(promptId, selection);

    // Clear active prompt and record the answer locally to show in chat bubble history
    setMessages((prevMessages) => {
      return prevMessages.map((msg) => {
        if (msg.activePrompt?.prompt_id === promptId) {
          const isFinished = msg.status === 'success' || msg.status === 'error' || !!msg.text;
          return {
            ...msg,
            activePrompt: undefined,
            promptAnswer: selection,
            thinkingMessage: isFinished ? undefined : 'Resuming task execution...'
          };
        }
        return msg;
      });
    });
  }, []);

  const triggerLLMServer = useCallback((action: 'start_llm' | 'stop_llm') => {
    defaultWsService.sendCommand(action);
  }, []);

  const refreshLLMStatus = useCallback(() => {
    defaultWsService.sendCommand('llm_status_request');
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    messageIdRef.current = null;
  }, []);

  return {
    messages,
    connectionStatus,
    llmStatus,
    sendMessage,
    respondToPrompt,
    triggerLLMServer,
    refreshLLMStatus,
    clearChat
  };
}
