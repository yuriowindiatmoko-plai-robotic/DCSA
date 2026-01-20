import { ref, computed, watch } from "vue";
import { useAuthStore } from "@/stores/auth";
import type { Ref } from "vue";

// Types
export interface Message {
  id: string;
  role: "user" | "model" | "system";
  content: string;
  timestamp: Date;
  status?: "pending" | "streaming" | "complete" | "error";
}

export interface ProcessedEvent {
  type: string;
  timestamp: Date;
  content?: string;
  metadata?: Record<string, unknown>;
}

export interface FoodAgentChatState {
  messages: Ref<Message[]>;
  messageEvents: Ref<Map<string, ProcessedEvent[]>>;
  isLoading: Ref<boolean>;
  sessionId: Ref<string>;
  userId: Ref<string>;
}

export interface FoodAgentChatActions {
  sendMessage: (content: string) => Promise<void>;
  createSession: () => Promise<void>;
  clearMessages: () => void;
  loadSessionHistory: () => Promise<void>;
  updateMessage: (messageId: string, content: string) => void;
}

/**
 * Composable for managing Food Analyst Agent chat state
 * Replaces React hooks (useSession, useMessages, useStreaming)
 */
export function useFoodAgentChat(): FoodAgentChatState & FoodAgentChatActions {
  const authStore = useAuthStore();

  // State
  const messages = ref<Message[]>([]);
  const messageEvents = ref<Map<string, ProcessedEvent[]>>(new Map());
  const isLoading = ref<boolean>(false);
  const sessionId = ref<string>("");
  const userId = ref<string>(authStore.userId || "anonymous");

  // Storage key for localStorage
  const storageKey = computed(
    () => `food_agent_chat_${userId.value}_${sessionId.value}`,
  );

  /**
   * Generate a unique message ID
   */
  const generateMessageId = (): string => {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  };

  /**
   * Create a new chat session
   */
  const createSession = async (): Promise<void> => {
    try {
      isLoading.value = true;
      // VITE_API_URL
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/food-analyst/sessions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authStore.token}`,
          },
          body: JSON.stringify({
            userId: userId.value,
            systemInstruction: {
              parts: [
                {
                  text: "You are a helpful Indonesian food analyst assistant.",
                },
              ],
            },
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }

      const data = await response.json();
      sessionId.value = data.sessionId;

      // Clear previous messages when creating new session
      clearMessages();
    } catch (error) {
      console.error("Error creating session:", error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Load session history from localStorage
   */
  const loadSessionHistory = async (): Promise<void> => {
    try {
      const stored = localStorage.getItem(storageKey.value);
      if (stored) {
        const parsedMessages = JSON.parse(stored) as Message[];
        messages.value = parsedMessages.map((msg) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      }
    } catch (error) {
      console.error("Error loading session history:", error);
    }
  };

  /**
   * Send a message to the agent
   */
  const sendMessage = async (content: string): Promise<void> => {
    if (!content.trim() || isLoading.value) {
      return;
    }

    // Ensure session exists
    if (!sessionId.value) {
      await createSession();
    }

    // Add user message
    const userMessage: Message = {
      id: generateMessageId(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
      status: "complete",
    };
    messages.value.push(userMessage);

    // Create placeholder for AI response
    const aiMessageId = generateMessageId();
    const aiMessage: Message = {
      id: aiMessageId,
      role: "model",
      content: "",
      timestamp: new Date(),
      status: "streaming",
    };
    messages.value.push(aiMessage);

    try {
      isLoading.value = true;

      // Send message with SSE streaming
      await streamAgentResponse(content, aiMessageId);
    } catch (error) {
      console.error("Error sending message:", error);

      // Update message status to error
      const errorIndex = messages.value.findIndex((m) => m.id === aiMessageId);
      if (errorIndex !== -1) {
        messages.value[errorIndex].status = "error";
        messages.value[errorIndex].content =
          "Sorry, there was an error processing your request.";
      }
    } finally {
      isLoading.value = false;
    }

    // Save to localStorage
    saveToStorage();
  };

  /**
   * Stream agent response using Server-Sent Events
   */
  const streamAgentResponse = async (
    query: string,
    aiMessageId: string,
  ): Promise<void> => {
    const abortController = new AbortController();

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/food-analyst/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authStore.token}`,
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            appName: "food_analyst_agent_adk",
            userId: userId.value,
            sessionId: sessionId.value,
            newMessage: {
              role: "user",
              parts: [{ text: query }],
            },
          }),
          signal: abortController.signal,
        },
      );

      if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
      }

      // Process SSE stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No readable stream available");
      }

      const decoder = new TextDecoder();
      let lineBuffer = "";
      let eventDataBuffer = "";

      // Find AI message index for updates
      const aiMessageIndex = messages.value.findIndex(
        (m) => m.id === aiMessageId,
      );

      // Read stream
      while (true) {
        const { done, value } = await reader.read();

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          lineBuffer += chunk;
        }

        // Process complete lines
        let eolIndex;
        while (
          (eolIndex = lineBuffer.indexOf("\n")) >= 0 ||
          (done && lineBuffer.length > 0)
        ) {
          let line: string;
          if (eolIndex >= 0) {
            line = lineBuffer.substring(0, eolIndex);
            lineBuffer = lineBuffer.substring(eolIndex + 1);
          } else {
            line = lineBuffer;
            lineBuffer = "";
          }

          // Process SSE event
          if (line.trim() === "") {
            // Empty line: dispatch event
            if (eventDataBuffer.length > 0) {
              await processSSEEvent(eventDataBuffer, aiMessageIndex);
              eventDataBuffer = "";
            }
          } else if (line.startsWith("data:")) {
            // Accumulate data lines
            eventDataBuffer += line.substring(5).trimStart() + "\n";
          }
        }

        if (done) {
          // Process remaining data
          if (eventDataBuffer.length > 0) {
            await processSSEEvent(eventDataBuffer, aiMessageIndex);
          }
          break;
        }
      }

      // Mark message as complete
      if (aiMessageIndex !== -1) {
        messages.value[aiMessageIndex].status = "complete";
      }
    } catch (error) {
      if ((error as Error).name === "AbortError") {
        console.log("Request was cancelled");
      } else {
        throw error;
      }
    }
  };

  /**
   * Process individual SSE event
   */
  const processSSEEvent = async (
    jsonData: string,
    aiMessageIndex: number,
  ): Promise<void> => {
    try {
      const data = JSON.parse(jsonData);

      // Handle different event types from ADK agent
      if (data.content?.parts?.[0]?.text) {
        // Append text to AI message
        const text = data.content.parts[0].text;
        if (aiMessageIndex !== -1) {
          messages.value[aiMessageIndex].content += text;
        }
      }

      // Handle tool use events (e.g., food database queries)
      if (data.eventType === "tool_use") {
        const event: ProcessedEvent = {
          type: "tool_use",
          timestamp: new Date(),
          metadata: data.metadata,
        };

        const messageId = messages.value[aiMessageIndex]?.id;
        if (messageId) {
          const currentEvents = messageEvents.value.get(messageId) || [];
          messageEvents.value.set(messageId, [...currentEvents, event]);
        }
      }

      // Force Vue reactivity update
      await new Promise((resolve) => setTimeout(resolve, 0));
    } catch (error) {
      console.error("Error processing SSE event:", error);
    }
  };

  /**
   * Update a message's content
   */
  const updateMessage = (messageId: string, content: string): void => {
    const index = messages.value.findIndex((m) => m.id === messageId);
    if (index !== -1) {
      messages.value[index].content = content;
      saveToStorage();
    }
  };

  /**
   * Clear all messages
   */
  const clearMessages = (): void => {
    messages.value = [];
    messageEvents.value.clear();
    saveToStorage();
  };

  /**
   * Save messages to localStorage
   */
  const saveToStorage = (): void => {
    try {
      localStorage.setItem(storageKey.value, JSON.stringify(messages.value));
    } catch (error) {
      console.error("Error saving to storage:", error);
    }
  };

  // Auto-save when messages change
  watch(
    messages,
    () => {
      saveToStorage();
    },
    { deep: true },
  );

  return {
    // State
    messages,
    messageEvents,
    isLoading,
    sessionId,
    userId,

    // Actions
    sendMessage,
    createSession,
    clearMessages,
    loadSessionHistory,
    updateMessage,
  };
}
