import { useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { MobileTopBar } from './MobileTopBar';
import { Drawer } from '@/components/ui/Drawer';
import { useChat } from '@/hooks/useChat';
import { useSettings } from '@/hooks/useSettings';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { WelcomeScreen } from '@/components/pages/WelcomeScreen';
import { ChatArea } from '@/components/chat/ChatArea';
import { ChatInput } from '@/components/chat/ChatInput';
import { SettingsDialog } from '@/components/dialogs/SettingsDialog';
import { ContextPanel } from '@/components/context-panel/ContextPanel';
import { CommandPalette } from '@/components/dialogs/CommandPalette';
import { useUIStore } from '@/store/uiStore';
import type { UserProfile } from '@/types';
import { AlertCircle } from 'lucide-react';

const user: UserProfile = {
  name: 'Alex Carter',
  email: 'alex@aether.ai',
  plan: 'Pro Plan',
  initials: 'AC',
};

export function AppShell() {
  const isMobile = useIsMobile();
  const isOnline = useOnlineStatus();
  const [mobileOpen, setMobileOpen] = useState(false);
  
  const { sidebarCollapsed, toggleSidebar, settingsOpen, setSettingsOpen } = useUIStore();
  const chat = useChat();
  const { settings, update } = useSettings();

  useEffect(() => {
    if (settings.reducedMotion) {
      document.documentElement.setAttribute('data-reduced-motion', 'true');
    } else {
      document.documentElement.removeAttribute('data-reduced-motion');
    }
    
    if (settings.highContrast) {
      document.documentElement.setAttribute('data-high-contrast', 'true');
    } else {
      document.documentElement.removeAttribute('data-high-contrast');
    }
  }, [settings.reducedMotion, settings.highContrast]);

  const handleNewChat = () => {
    chat.newConversation();
    if (isMobile) setMobileOpen(false);
  };

  const handleSuggestion = (prompt: string) => {
    chat.sendMessage(prompt);
  };

  const handleExport = () => {
    if (!chat.activeConversation) return;
    
    // Sanitize export by removing internal runtime state like "liked" if needed, 
    // but definitely no API keys are in here since it's just the conversation.
    const exportData = {
      ...chat.activeConversation,
      messages: chat.activeConversation.messages.map(m => ({
        role: m.role,
        content: m.content,
        createdAt: m.createdAt,
      }))
    };
    
    const data = JSON.stringify(exportData, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${chat.activeConversation.title.replace(/\s+/g, '-').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const showWelcome = !chat.activeConversation || chat.activeConversation.messages.length === 0;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Offline Banner */}
      <AnimatePresence>
        {!isOnline && (
          <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -50, opacity: 0 }}
            className="absolute top-0 left-0 right-0 z-[100] bg-destructive text-destructive-foreground py-1.5 px-4 text-xs font-semibold flex items-center justify-center gap-2 shadow-lg"
          >
            <AlertCircle className="w-4 h-4" />
            You are currently offline. Check your connection.
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <Sidebar
        conversations={chat.conversations}
        activeId={chat.activeId}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
        onNewChat={handleNewChat}
        onSelect={(id) => {
          chat.setActiveId(id);
          if (isMobile) setMobileOpen(false);
        }}
        onDelete={chat.deleteConversation}
        onTogglePin={chat.togglePin}
        onRename={chat.renameConversation}
        onDuplicate={chat.duplicateConversation}
        searchQuery={chat.searchQuery}
        onSearchChange={chat.setSearchQuery}
        onSettings={() => setSettingsOpen(true)}
        user={user}
      />

      {/* Mobile drawer */}
      <Drawer open={mobileOpen && isMobile} onClose={() => setMobileOpen(false)} side="left">
        <div className="h-full">
          <Sidebar
            conversations={chat.conversations}
            activeId={chat.activeId}
            collapsed={false}
            onToggleCollapse={() => setMobileOpen(false)}
            onNewChat={handleNewChat}
            onSelect={(id) => {
              chat.setActiveId(id);
              setMobileOpen(false);
            }}
            onDelete={chat.deleteConversation}
            onTogglePin={chat.togglePin}
            onRename={chat.renameConversation}
            onDuplicate={chat.duplicateConversation}
            searchQuery={chat.searchQuery}
            onSearchChange={chat.setSearchQuery}
            onSettings={() => {
              setSettingsOpen(true);
              setMobileOpen(false);
            }}
            user={user}
          />
        </div>
      </Drawer>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden relative z-10 pt-safe">
        <MobileTopBar
          onMenuClick={() => setMobileOpen(true)}
          onSettingsClick={() => setSettingsOpen(true)}
          title="AETHER AI"
        />

        <div className="relative flex-1 overflow-hidden flex flex-col">
          <div className="relative flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              {showWelcome ? (
                <motion.div
                  key="welcome"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <WelcomeScreen onSuggestionClick={handleSuggestion} />
                </motion.div>
              ) : (
                <motion.div
                  key="chat"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="h-full"
                >
                  <ChatArea
                    conversation={chat.activeConversation}
                    isStreaming={chat.isStreaming}
                    onRegenerate={chat.regenerate}
                    onLike={chat.toggleLike}
                    onClear={() => chat.activeId && chat.clearMessages(chat.activeId)}
                    onExport={handleExport}
                    onEdit={chat.editMessage}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
          <div className="w-full shrink-0">
            <ChatInput 
              onSend={chat.sendMessage} 
              onStop={chat.stopStreaming} 
              isStreaming={chat.isStreaming} 
            />
          </div>
        </div>
      </div>

      {/* Right Context Panel */}
      <ContextPanel />
      
      <CommandPalette />

      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onUpdate={update}
        onExport={handleExport}
        onClear={() => chat.activeId && chat.clearMessages(chat.activeId)}
      />
    </div>
  );
}

