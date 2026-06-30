import type { PipelineEvent } from '../types/events';

type EventCallback = (event: PipelineEvent) => void;
type ConnectionCallback = (connected: boolean) => void;

export class AetherWebSocketService {
  private url: string;
  private ws: WebSocket | null = null;
  private onEventCallback: EventCallback | null = null;
  private onConnectionCallback: ConnectionCallback | null = null;
  private reconnectTimeout: number = 3000;
  private reconnectTimer: number | null = null;
  private shouldReconnect: boolean = true;

  constructor(url: string = 'ws://127.0.0.1:8000/ws') {
    this.url = url;
  }

  public connect(onEvent: EventCallback, onConnectionChange: ConnectionCallback) {
    this.onEventCallback = onEvent;
    this.onConnectionCallback = onConnectionChange;
    this.shouldReconnect = true;
    this.createWebSocket();
  }

  private createWebSocket() {
    if (this.ws) {
      try {
        this.ws.close();
      } catch (e) {
        // Already closed
      }
    }

    console.log(`Connecting to Aether WebSocket: ${this.url}`);
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket Connection Opened.');
        this.onConnectionChange(true);
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as PipelineEvent;
          if (this.onEventCallback) {
            this.onEventCallback(data);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket Connection Closed.');
        this.onConnectionChange(false);
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
      };
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
      this.scheduleReconnect();
    }
  }

  private onConnectionChange(connected: boolean) {
    if (this.onConnectionCallback) {
      this.onConnectionCallback(connected);
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      if (this.shouldReconnect) {
        this.createWebSocket();
      }
    }, this.reconnectTimeout);
  }

  public sendMessage(message: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'user_message',
        message: message
      }));
    } else {
      console.error('WebSocket is not open. Cannot send message:', message);
    }
  }

  public sendCommand(type: 'start_llm' | 'stop_llm' | 'llm_status_request') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type }));
    } else {
      console.error(`WebSocket is not open. Cannot send command: ${type}`);
    }
  }

  public sendPromptResponse(promptId: string, selection: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'prompt_response',
        prompt_id: promptId,
        selection: selection
      }));
    } else {
      console.error('WebSocket is not open. Cannot send prompt response:', promptId);
    }
  }

  public disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch (e) {
        // Already closed
      }
      this.ws = null;
    }
  }
}
export const defaultWsService = new AetherWebSocketService();
