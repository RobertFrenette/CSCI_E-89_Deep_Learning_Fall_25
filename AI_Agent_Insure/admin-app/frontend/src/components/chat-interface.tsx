"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { aiAgent, ChatRequest, ChatResponse } from "@/lib/ai-agent-client";
import { Send, Loader2, Bot, User, AlertCircle, X } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  query_type?: string;
  timestamp: Date;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError(null);
    setIsLoading(true);

    // Prepare chat request with conversation history
    const chatRequest: ChatRequest = {
      messages: [
        ...messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
        {
          role: "user",
          content: userMessage.content,
        },
      ],
      user_id: "admin", // Admin user ID for logging
      temperature: 0.1,
      top_k: 3,
    };

    // Log request to console
    console.log("📤 AI Agent Request:", {
      request: chatRequest,
      timestamp: new Date().toISOString(),
    });

    // Create placeholder assistant message for streaming
    const assistantMessageId = Date.now();
    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      sources: [],
      timestamp: new Date(),
    };

    // Add empty assistant message that we'll update as chunks arrive
    setMessages((prev) => [...prev, assistantMessage]);

    // Track accumulated content for logging
    let accumulatedContent = "";

    // Get abort controller immediately (before starting stream)
    abortControllerRef.current = aiAgent.chatStream(
      chatRequest,
      // onChunk: update the assistant message with each chunk
      (chunk: string) => {
        // Check if cancelled before processing chunk
        if (abortControllerRef.current?.signal.aborted) {
          return;
        }
        accumulatedContent += chunk;
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg.role === "assistant") {
            lastMsg.content += chunk;
          }
          return updated;
        });
      },
      // onComplete: update with final metadata
      (metadata: { sources: string[]; query_type?: string }) => {
        // Don't update if cancelled
        if (abortControllerRef.current?.signal.aborted) {
          return;
        }
        setMessages((prev) => {
          const updated = [...prev];
          const lastMsg = updated[updated.length - 1];
          if (lastMsg.role === "assistant") {
            lastMsg.sources = metadata.sources;
            lastMsg.query_type = metadata.query_type;
          }
          return updated;
        });
        
        // Log complete response with text content
        console.log("📥 AI Agent Response:", {
          answer: accumulatedContent,
          sources: metadata.sources,
          query_type: metadata.query_type,
          timestamp: new Date().toISOString(),
        });
        
        setIsLoading(false);
        abortControllerRef.current = null;
        
        // Focus input after response completes
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      },
      // onError
      (error: Error) => {
      // Don't show error if cancelled
      if (abortControllerRef.current?.signal.aborted) {
        setIsLoading(false);
        abortControllerRef.current = null;
        // Focus input after cancel
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
        return;
      }
        const errorMessage = error.message || "Failed to get response from AI Agent";
        setError(errorMessage);
        console.error("Chat error:", error);
        // Remove the empty assistant message on error
        setMessages((prev) => prev.slice(0, -1));
        setIsLoading(false);
        abortControllerRef.current = null;
        
        // Focus input after error
        setTimeout(() => {
          inputRef.current?.focus();
        }, 100);
      }
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setError(null);
      // Update the last assistant message to indicate it was cancelled
      setMessages((prev) => {
        const updated = [...prev];
        const lastMsg = updated[updated.length - 1];
        if (lastMsg.role === "assistant" && lastMsg.content === "") {
          // Remove empty message if nothing was received
          return updated.slice(0, -1);
        } else if (lastMsg.role === "assistant") {
          // Keep partial response but mark as cancelled
          lastMsg.content += "\n\n*[Query cancelled by user]*";
        }
        return updated;
      });
      abortControllerRef.current = null;
      
      // Focus input after cancel
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  const getQueryTypeBadge = (queryType?: string) => {
    if (!queryType) return null;

    const colors: Record<string, string> = {
      sql: "bg-blue-500",
      rag: "bg-purple-500",
      hybrid: "bg-green-500",
    };

    return (
      <Badge
        variant="secondary"
        className={`${colors[queryType] || "bg-gray-500"} text-white`}
      >
        {queryType.toUpperCase()}
      </Badge>
    );
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Messages Area */}
      <Card className="flex-1 flex flex-col min-h-0 mb-4 overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI Agent Chat
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Start a conversation with the AI Agent</p>
              <p className="text-sm mt-2">
                Ask questions about policies, claims, customers, or company information
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="h-4 w-4 text-primary" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <div className="flex items-start gap-2 mb-2">
                  {message.role === "user" ? (
                    <User className="h-4 w-4 mt-0.5" />
                  ) : (
                    <Bot className="h-4 w-4 mt-0.5" />
                  )}
                  <span className="font-semibold text-sm">
                    {message.role === "user" ? "You" : "AI Agent"}
                  </span>
                  {message.query_type && getQueryTypeBadge(message.query_type)}
                </div>
                <div className="markdown-content">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                      li: ({ children }) => <li className="ml-2">{children}</li>,
                      h1: ({ children }) => <h1 className="text-xl font-bold mb-2 mt-4 first:mt-0">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-3 first:mt-0">{children}</h3>,
                      code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                      pre: ({ children }) => <pre className="bg-muted p-2 rounded mb-2 overflow-x-auto">{children}</pre>,
                      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                      em: ({ children }) => <em className="italic">{children}</em>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>

                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-border/50">
                    <div className="text-xs font-semibold mb-1">Sources:</div>
                    <div className="flex flex-wrap gap-1">
                      {message.sources.map((source, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {source}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>

              {message.role === "user" && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="h-4 w-4 text-primary" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="bg-muted rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">AI Agent is thinking...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-destructive/10 flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-destructive" />
              </div>
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <div className="flex items-center gap-2 text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">Error: {error}</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </CardContent>
      </Card>

      {/* Input Area */}
      <div className="flex gap-2">
        <Input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about policies, claims, customers, or company info..."
          disabled={isLoading}
          className="flex-1"
        />
        {isLoading ? (
          <Button
            onClick={handleCancel}
            variant="destructive"
            size="default"
          >
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            disabled={!input.trim()}
            size="default"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

