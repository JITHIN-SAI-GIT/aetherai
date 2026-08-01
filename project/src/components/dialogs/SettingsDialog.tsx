import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Palette, Globe, Thermometer, Cpu, Brain, Download, Trash2, Info, Check,
  Settings as SettingsIcon, Database, Search, Zap, Shield, Eye, Terminal
} from 'lucide-react';
import { Dialog } from '@/components/ui/Dialog';
import { Slider } from '@/components/ui/Slider';
import { Switch } from '@/components/ui/Switch';
import { accentList } from '@/utils/accent';
import { useQuery } from '@tanstack/react-query';
import { fetchModels } from '@/services/api';
import { useUIStore } from '@/store/uiStore';
import { useKeysStore } from '@/store/keysStore';
import type { AccentColor, Settings } from '@/types';
import { cn } from '@/utils/cn';

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  settings: Settings;
  onUpdate: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
  onExport: () => void;
  onClear: () => void;
}

const languages = ['English', 'Spanish', 'French', 'German', 'Japanese', 'Chinese', 'Portuguese'];

const TABS = [
  { id: 'general', label: 'General', icon: SettingsIcon },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'providers', label: 'Providers', icon: Database },
  { id: 'memory', label: 'Memory', icon: Brain },
  { id: 'search', label: 'Search', icon: Search },
  { id: 'performance', label: 'Performance', icon: Zap },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'accessibility', label: 'Accessibility', icon: Eye },
  { id: 'developer', label: 'Developer', icon: Terminal },
];

export function SettingsDialog({
  open,
  onClose,
  settings,
  onUpdate,
  onExport,
  onClear,
}: SettingsDialogProps) {
  const [activeTab, setActiveTab] = useState('general');
  const { theme, setTheme } = useUIStore();
  const { keys, setKey } = useKeysStore();

  const { data: models = [], isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Settings"
      description="Configure AETHER AI"
      className="max-w-4xl w-full h-[80vh] flex flex-col overflow-hidden"
    >
      <div className="flex h-full flex-col md:flex-row overflow-hidden mt-4 border border-white/[0.08] rounded-2xl glass-strong">
        
        {/* Sidebar Tabs */}
        <div className="w-full md:w-56 border-b md:border-b-0 md:border-r border-white/[0.08] bg-black/[0.02] dark:bg-white/[0.02] flex flex-row md:flex-col overflow-x-auto md:overflow-y-auto scrollbar-thin p-3 gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all shrink-0 md:shrink",
                activeTab === tab.id 
                  ? "bg-primary/10 text-primary" 
                  : "text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 hover:text-foreground"
              )}
            >
              <tab.icon className="h-4 w-4" />
              <span className="hidden md:inline-block">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto scrollbar-thin p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.15 }}
              className="space-y-8 max-w-xl"
            >
              
              {activeTab === 'general' && (
                <>
                  <Section icon={Globe} title="Language">
                    <select
                      value={settings.language}
                      onChange={(e) => onUpdate('language', e.target.value)}
                      className={cn(
                        'w-full rounded-xl bg-white/5 border border-white/[0.08] px-3 py-2.5 text-sm',
                        'text-foreground focus:outline-none focus:ring-2 focus:ring-ring/50',
                      )}
                    >
                      {languages.map((l) => (
                        <option key={l} value={l} className="bg-background">
                          {l}
                        </option>
                      ))}
                    </select>
                  </Section>

                  <div className="space-y-3 pt-6 border-t border-white/[0.08]">
                    <h3 className="text-sm font-semibold">Data & Privacy</h3>
                    <button
                      onClick={onExport}
                      className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm glass-panel hover:bg-white/5 transition-colors"
                    >
                      <Download className="h-4 w-4 text-primary" />
                      Export Data
                    </button>
                    <button
                      onClick={onClear}
                      className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm text-destructive glass-panel hover:bg-destructive/10 transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                      Clear All History
                    </button>
                  </div>
                </>
              )}

              {activeTab === 'appearance' && (
                <>
                  <Section icon={Palette} title="UI Theme">
                    <div className="flex gap-2">
                       {['light', 'dark', 'system'].map(t => (
                         <button
                           key={t}
                           onClick={() => setTheme(t as any)}
                           className={cn(
                             "px-4 py-2 rounded-xl text-sm capitalize transition-all",
                             theme === t ? "glass-strong ring-1 ring-primary text-primary" : "glass-panel hover:bg-white/5"
                           )}
                         >
                           {t}
                         </button>
                       ))}
                    </div>
                  </Section>

                  <Section icon={Palette} title="Accent Color">
                    <div className="flex flex-wrap gap-2.5">
                      {accentList.map((a) => (
                        <button
                          key={a.id}
                          onClick={() => onUpdate('accent', a.id as AccentColor)}
                          className={cn(
                            'flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-all',
                            settings.accent === a.id
                              ? 'glass-strong ring-1 ring-primary'
                              : 'glass-panel hover:bg-black/5 dark:hover:bg-white/5',
                          )}
                        >
                          <span
                            className="h-4 w-4 rounded-full"
                            style={{ background: a.swatch }}
                          />
                          {a.label}
                          {settings.accent === a.id && <Check className="h-3.5 w-3.5 text-primary" />}
                        </button>
                      ))}
                    </div>
                  </Section>
                </>
              )}

              {activeTab === 'models' && (
                <>
                  <Section icon={Thermometer} title="Temperature">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Creativity level</span>
                        <span className="font-mono text-primary">{settings.temperature.toFixed(2)}</span>
                      </div>
                      <Slider
                        value={settings.temperature}
                        min={0}
                        max={1}
                        step={0.05}
                        onChange={(v) => onUpdate('temperature', v)}
                      />
                      <div className="flex justify-between text-[10px] text-muted-foreground/60 uppercase font-bold tracking-wider">
                        <span>Precise</span>
                        <span>Balanced</span>
                        <span>Creative</span>
                      </div>
                    </div>
                  </Section>

                  <Section icon={Cpu} title="Default Model">
                    {modelsLoading ? (
                      <div className="text-sm text-muted-foreground animate-pulse">Loading models...</div>
                    ) : (
                      <div className="grid grid-cols-1 gap-2">
                        {models.map((m: any) => (
                          <button
                            key={m.id}
                            onClick={() => onUpdate('model', m.id)}
                            className={cn(
                              'flex flex-col items-start gap-0.5 rounded-xl p-3 text-left transition-all',
                              settings.model === m.id
                                ? 'glass-strong ring-1 ring-primary'
                                : 'glass-panel hover:bg-black/5 dark:hover:bg-white/5',
                            )}
                          >
                            <div className="flex w-full items-center justify-between">
                              <span className="text-sm font-bold">{m.name || m.id}</span>
                              {settings.model === m.id && <Check className="h-4 w-4 text-primary" />}
                            </div>
                            <span className="text-xs text-muted-foreground leading-relaxed">{m.description || 'Advanced AI Model'}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </Section>
                </>
              )}

              {activeTab === 'memory' && (
                <Section icon={Brain} title="Memory System">
                  <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                    <div>
                      <p className="text-sm font-bold">Long-Term Memory</p>
                      <p className="text-xs text-muted-foreground mt-1">AETHER AI will remember context and preferences across all conversations.</p>
                    </div>
                    <Switch
                      checked={settings.memory}
                      onChange={(v) => onUpdate('memory', v)}
                    />
                  </div>
                </Section>
              )}

              {activeTab === 'providers' && (
                <Section icon={Database} title="API Providers">
                  <div className="space-y-4">
                    <p className="text-sm text-muted-foreground mb-4">Manage your API keys for external models. Keys are stored safely in memory for this session only.</p>
                    {['OpenAI', 'Anthropic', 'Gemini', 'Groq'].map(p => (
                      <div key={p} className="flex flex-col gap-2 glass-panel p-3 rounded-xl">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-sm">{p}</span>
                          <Switch checked={!!keys[p.toLowerCase()]} onChange={() => {}} />
                        </div>
                        <input
                          type="password"
                          placeholder="sk-..."
                          value={keys[p.toLowerCase()] || ''}
                          onChange={(e) => setKey(p.toLowerCase(), e.target.value)}
                          className="w-full bg-black/20 dark:bg-white/5 rounded-lg px-3 py-2 text-sm border border-transparent focus:border-primary/50 focus:outline-none transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {activeTab === 'search' && (
                <Section icon={Search} title="Search Configuration">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Web Search</p>
                        <p className="text-xs text-muted-foreground mt-1">Allow the agent to search the web for real-time info.</p>
                      </div>
                      <Switch checked={settings.webSearch !== false} onChange={(v) => onUpdate('webSearch' as any, v)} />
                    </div>
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Show Citations</p>
                        <p className="text-xs text-muted-foreground mt-1">Display search sources above messages.</p>
                      </div>
                      <Switch checked={settings.showCitations !== false} onChange={(v) => onUpdate('showCitations' as any, v)} />
                    </div>
                  </div>
                </Section>
              )}

              {activeTab === 'performance' && (
                <Section icon={Zap} title="Performance Options">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Smart Caching</p>
                        <p className="text-xs text-muted-foreground mt-1">Cache identical queries to reduce latency.</p>
                      </div>
                      <Switch checked={settings.smartCaching !== false} onChange={(v) => onUpdate('smartCaching' as any, v)} />
                    </div>
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Streaming Response</p>
                        <p className="text-xs text-muted-foreground mt-1">Stream tokens immediately (lower TTFB).</p>
                      </div>
                      <Switch checked={settings.streamingResponse !== false} onChange={(v) => onUpdate('streamingResponse' as any, v)} />
                    </div>
                  </div>
                </Section>
              )}

              {activeTab === 'security' && (
                <Section icon={Shield} title="Security & Guardrails">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Prompt Injection Filter</p>
                        <p className="text-xs text-muted-foreground mt-1">Block malicious prompt patterns automatically.</p>
                      </div>
                      <Switch checked={settings.promptInjectionFilter !== false} onChange={(v) => onUpdate('promptInjectionFilter' as any, v)} />
                    </div>
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Secret Redaction</p>
                        <p className="text-xs text-muted-foreground mt-1">Prevent PII and secrets from being sent to providers.</p>
                      </div>
                      <Switch checked={settings.secretRedaction !== false} onChange={(v) => onUpdate('secretRedaction' as any, v)} />
                    </div>
                  </div>
                </Section>
              )}

              {activeTab === 'accessibility' && (
                <Section icon={Eye} title="Accessibility">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Reduce Motion</p>
                        <p className="text-xs text-muted-foreground mt-1">Disable complex animations and transitions.</p>
                      </div>
                      <Switch checked={settings.reducedMotion === true} onChange={(v) => onUpdate('reducedMotion' as any, v)} />
                    </div>
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">High Contrast</p>
                        <p className="text-xs text-muted-foreground mt-1">Increase text contrast and border visibility.</p>
                      </div>
                      <Switch checked={settings.highContrast === true} onChange={(v) => onUpdate('highContrast' as any, v)} />
                    </div>
                  </div>
                </Section>
              )}

              {activeTab === 'developer' && (
                <Section icon={Terminal} title="Developer Settings">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 glass-panel rounded-xl">
                      <div>
                        <p className="text-sm font-bold">Debug Mode</p>
                        <p className="text-xs text-muted-foreground mt-1">Show verbose logs and timing information.</p>
                      </div>
                      <Switch checked={settings.debugMode === true} onChange={(v) => onUpdate('debugMode' as any, v)} />
                    </div>
                    <div>
                      <p className="text-sm font-bold mb-2">System Prompt Template</p>
                      <textarea
                        className="w-full bg-black/10 dark:bg-white/5 rounded-xl p-3 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary border border-transparent scrollbar-thin"
                        rows={6}
                        value={settings.systemPrompt || "You are AETHER AI, an advanced AI operating system.\nYou are helpful, highly capable, and intelligent."}
                        onChange={(e) => onUpdate('systemPrompt' as any, e.target.value)}
                      />
                    </div>
                  </div>
                </Section>
              )}

            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </Dialog>
  );
}

function Section({
  icon: Icon,
  title,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="mb-6">
      <div className="mb-4 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-muted-foreground">
        <Icon className="h-4 w-4 text-primary" />
        {title}
      </div>
      {children}
    </div>
  );
}
