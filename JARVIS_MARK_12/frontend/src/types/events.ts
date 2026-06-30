export type ConnectionStatus = 'connected' | 'disconnected';

export interface LLMStatus {
  router_running: boolean;
  planner_running: boolean;
  router_model: string;
  planner_model: string;
  router_port: number;
  planner_port: number;
  endpoint: string;
}

export type PipelineEvent =
  | { type: 'thinking'; message: string }
  | { type: 'plan'; steps: string[] }
  | { type: 'step_start'; step: string }
  | { type: 'step_complete'; step: string; success: boolean }
  | { type: 'tool_start'; tool: string }
  | { type: 'tool_complete'; tool: string; success: boolean }
  | { type: 'error'; message: string; error_code?: string }
  | { type: 'final_response'; message: string }
  | { type: 'user_prompt'; prompt_id: string; title: string; options: string[] }
  | { 
      type: 'llm_status'; 
      router_running: boolean; 
      planner_running: boolean; 
      router_model: string; 
      planner_model: string; 
      router_port: number; 
      planner_port: number; 
      endpoint: string;
    };

export interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  status?: 'pending' | 'success' | 'error';
  plan?: string[];
  currentStepIndex?: number;
  stepsStatus?: { [stepDescription: string]: 'pending' | 'running' | 'success' | 'error' };
  toolEvents?: { tool: string; success?: boolean; running?: boolean }[];
  thinkingMessage?: string;
  errorMessage?: string;
  errorCode?: string;
  activePrompt?: { prompt_id: string; title: string; options: string[] };
  promptAnswer?: string;
}
