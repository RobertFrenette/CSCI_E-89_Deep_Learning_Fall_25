import { ChatInterface } from "@/components/chat-interface";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Card, CardContent } from "@/components/ui/card";

export default function ChatPage() {
  return (
    <div className="flex flex-col gap-6 p-6 h-[calc(100vh-2rem)]">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">AI Agent Chat</h1>
          <p className="text-muted-foreground">
            Ask questions about policies, claims, customers, or company information
          </p>
        </div>
      </div>

      <Card className="flex-1 flex flex-col min-h-0">
        <CardContent className="flex-1 p-6 min-h-0">
          <ChatInterface />
        </CardContent>
      </Card>
    </div>
  );
}

