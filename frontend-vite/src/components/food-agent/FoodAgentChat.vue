<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from "vue";
import { useFoodAgentChat } from "@/composables/useFoodAgentChat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Loader2, Send, Bot, User, Sparkles } from "lucide-vue-next";
import { toast } from "vue-sonner";

// Composable
const {
  messages,
  messageEvents,
  isLoading,
  sessionId,
  sendMessage,
  createSession,
  clearMessages,
  loadSessionHistory,
} = useFoodAgentChat();

// Local state
const inputMessage = ref<string>("");
const messagesContainer = ref<HTMLElement | null>(null);
const isInitialized = ref<boolean>(false);

/**
 * Initialize chat session on mount
 */
onMounted(async () => {
  try {
    await createSession();
    await loadSessionHistory();
    isInitialized.value = true;

    // Scroll to bottom
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("Failed to initialize chat:", error);
    toast.error("Failed to connect to Food Analyst Agent");
  }
});

/**
 * Send message handler
 */
const handleSendMessage = async (): Promise<void> => {
  if (!inputMessage.value.trim() || isLoading.value) {
    return;
  }

  const message = inputMessage.value;
  inputMessage.value = "";

  try {
    await sendMessage(message);

    // Scroll to bottom after message is sent
    await nextTick();
    scrollToBottom();
  } catch (error) {
    console.error("Failed to send message:", error);
    toast.error("Failed to send message. Please try again.");
  }
};

/**
 * Handle Enter key press
 */
const handleKeyDown = (event: KeyboardEvent): void => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSendMessage();
  }
};

/**
 * Start new chat session
 */
const handleNewChat = async (): Promise<void> => {
  try {
    clearMessages();
    await createSession();
    toast.success("Started new chat session");
  } catch (error) {
    console.error("Failed to create new session:", error);
    toast.error("Failed to start new session");
  }
};

/**
 * Scroll messages container to bottom
 */
const scrollToBottom = (): void => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

/**
 * Get message status badge variant
 */
const getStatusBadgeVariant = (status?: string) => {
  switch (status) {
    case "streaming":
      return "default";
    case "error":
      return "destructive";
    default:
      return "secondary";
  }
};

/**
 * Get message status text
 */
const getStatusText = (status?: string): string | undefined => {
  switch (status) {
    case "streaming":
      return "Thinking...";
    case "error":
      return "Error";
    default:
      return undefined;
  }
};
</script>

<template>
  <div class="flex flex-col h-full bg-background">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-6 py-4">
      <div class="flex items-center gap-3">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10"
        >
          <Bot class="h-5 w-5 text-primary" />
        </div>
        <div>
          <h2 class="text-lg font-semibold">Food Analyst Agent</h2>
          <p class="text-sm text-muted-foreground">
            Ask about Indonesian food, nutrition, and dietary recommendations
          </p>
        </div>
      </div>
      <Button variant="outline" size="sm" @click="handleNewChat">
        <Sparkles class="mr-2 h-4 w-4" />
        New Chat
      </Button>
    </div>

    <!-- Messages Area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-6 space-y-6">
      <!-- Empty State -->
      <div
        v-if="messages.length === 0 && isInitialized"
        class="flex flex-col items-center justify-center h-full text-center space-y-4"
      >
        <div
          class="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10"
        >
          <Sparkles class="h-8 w-8 text-primary" />
        </div>
        <div class="space-y-2 max-w-md">
          <h3 class="text-lg font-semibold">Welcome to Food Analyst Agent</h3>
          <p class="text-sm text-muted-foreground">
            Ask me anything about Indonesian food, nutritional information,
            dietary recommendations, or menu planning!
          </p>
        </div>
        <div class="grid gap-2 text-sm text-left w-full max-w-lg">
          <Card
            class="p-3 hover:bg-accent cursor-pointer"
            @click="
              inputMessage =
                'Apa rekomendasi menu tinggi protein untuk muscle building?'
            "
          >
            <p class="text-muted-foreground">
              "Apa rekomendasi menu tinggi protein untuk muscle building?"
            </p>
          </Card>
          <Card
            class="p-3 hover:bg-accent cursor-pointer"
            @click="inputMessage = 'Berapa kalori pada Nasi Goreng Jawa?'"
          >
            <p class="text-muted-foreground">
              "Berapa kalori pada Nasi Goreng Jawa?"
            </p>
          </Card>
          <Card
            class="p-3 hover:bg-accent cursor-pointer"
            @click="
              inputMessage = 'Menu apa yang cocok untuk diet rendah garam?'
            "
          >
            <p class="text-muted-foreground">
              "Menu apa yang cocok untuk diet rendah garam?"
            </p>
          </Card>
        </div>
      </div>

      <!-- Messages List -->
      <div v-else class="space-y-6">
        <div
          v-for="message in messages"
          :key="message.id"
          class="flex gap-3"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- User Message -->
          <template v-if="message.role === 'user'">
            <div class="flex gap-3 max-w-[80%]">
              <div class="flex-1" />
              <div class="space-y-1">
                <div class="flex items-center justify-end gap-2">
                  <span class="text-xs text-muted-foreground">
                    {{ new Date(message.timestamp).toLocaleTimeString() }}
                  </span>
                  <span class="text-sm font-medium">You</span>
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-primary"
                  >
                    <User class="h-4 w-4 text-primary-foreground" />
                  </div>
                </div>
                <Card class="p-4 bg-primary text-primary-foreground">
                  <p class="whitespace-pre-wrap">{{ message.content }}</p>
                </Card>
              </div>
            </div>
          </template>

          <!-- AI Message -->
          <template v-else>
            <div class="flex gap-3 max-w-[80%]">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <div
                    class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900"
                  >
                    <Bot
                      class="h-4 w-4 text-emerald-600 dark:text-emerald-400"
                    />
                  </div>
                  <span class="text-sm font-medium">Food Analyst</span>
                  <span class="text-xs text-muted-foreground">
                    {{ new Date(message.timestamp).toLocaleTimeString() }}
                  </span>
                  <Badge
                    v-if="getStatusText(message.status)"
                    :variant="getStatusBadgeVariant(message.status)"
                  >
                    {{ getStatusText(message.status) }}
                  </Badge>
                </div>
                <Card class="p-4 bg-muted/50">
                  <div
                    class="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap"
                  >
                    <p v-if="message.content">{{ message.content }}</p>
                    <div
                      v-else
                      class="flex items-center gap-2 text-muted-foreground"
                    >
                      <Loader2 class="h-4 w-4 animate-spin" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </Card>

                <!-- Activity Timeline (optional) -->
                <div
                  v-if="
                    messageEvents.has(message.id) &&
                    messageEvents.get(message.id)!.length > 0
                  "
                  class="space-y-1 ml-2"
                >
                  <div
                    v-for="(event, idx) in messageEvents.get(message.id)"
                    :key="idx"
                    class="flex items-center gap-2 text-xs text-muted-foreground"
                  >
                    <div class="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    <span>{{ event.type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- Loading Indicator -->
        <div v-if="isLoading && messages.length > 0" class="flex gap-3">
          <div
            class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900"
          >
            <Bot class="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div class="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 class="h-4 w-4 animate-spin" />
            <span>Food Analyst is thinking...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="border-t p-4">
      <div class="flex items-end gap-3">
        <div class="flex-1">
          <Textarea
            v-model="inputMessage"
            placeholder="Ask about food, nutrition, or dietary recommendations..."
            class="min-h-[80px] max-h-48 resize-none"
            :disabled="isLoading || !isInitialized"
            @keydown="handleKeyDown"
          />
          <div
            class="mt-1 flex items-center justify-between text-xs text-muted-foreground"
          >
            <span>Press Enter to send, Shift + Enter for new line</span>
            <span v-if="inputMessage.length > 500"
              >{{ inputMessage.length }}/2000</span
            >
          </div>
        </div>
        <Button
          size="lg"
          :disabled="!inputMessage.trim() || isLoading || !isInitialized"
          @click="handleSendMessage"
        >
          <Loader2 v-if="isLoading" class="mr-2 h-4 w-4 animate-spin" />
          <Send v-else class="mr-2 h-4 w-4" />
          Send
        </Button>
      </div>
    </div>
  </div>
</template>
