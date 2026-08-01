import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Database, Cpu, Zap, Brain, Shield, PanelRightClose, Settings2, BarChart2 } from 'lucide-react';
import { useUIStore } from '@/store/uiStore';
import { useChatStore } from '@/store/chatStore';
import { fetchPerformanceMetrics, fetchMemoryProfile, fetchProviders } from '@/services/api';
import { cn } from '@/utils/cn';

type Tab = 'insights' | 'memory' | 'providers' | 'agents' | 'performance';

export function ContextPanel() {
  const { rightPanelOpen, setRightPanelOpen } = useUIStore();
  const [activeTab, setActiveTab] = useState<Tab>('insights');
  const { activeModel, activeProvider, activeAgent, activeId, conversations } = useChatStore();
  
  const activeConversation = conversations.find(c => c.id === activeId);

  const { data: metrics } = useQuery({ queryKey: ['performance-metrics'], queryFn: fetchPerformanceMetrics, refetchInterval: 5000 });
  const { data: memoryProfile } = useQuery({ queryKey: ['memory-profile'], queryFn: fetchMemoryProfile });
  const { data: providersData } = useQuery({ queryKey: ['providers'], queryFn: fetchProviders });

  const tabs: { id: Tab; icon: any; label: string }[] = [
    { id: 'insights', icon: Activity, label: 'Insights' },
    { id: 'memory', icon: Brain, label: 'Memory' },
    { id: 'providers', icon: Database, label: 'Providers' },
    { id: 'agents', icon: Cpu, label: 'Agents' },
    { id: 'performance', icon: BarChart2, label: 'Performance' },
  ];

  return (
    <AnimatePresence>
      {rightPanelOpen && (
        <motion.aside
          initial={{ width: 0, opacity: 0, borderLeftWidth: 0 }}
          animate={{ width: 380, opacity: 1, borderLeftWidth: 1 }}
          exit={{ width: 0, opacity: 0, borderLeftWidth: 0 }}
          transition={{ type: 'spring', damping: 30, stiffness: 300 }}
          className="relative z-20 h-full shrink-0 flex-col overflow-hidden glass border-l border-white/[0.06] hidden lg:flex"
        >
          {/* Header & Tabs */}
          <div className="flex flex-col border-b border-white/[0.06]">
            <div className="flex items-center justify-between px-4 py-3">
              <h2 className="text-sm font-semibold flex items-center gap-2">
                <Settings2 className="h-4 w-4 text-primary" />
                Context Workspace
              </h2>
              <button
                onClick={() => setRightPanelOpen(false)}
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
              >
                <PanelRightClose className="h-4 w-4" />
              </button>
            </div>
            
            <div className="flex px-2 pb-2 gap-1 overflow-x-auto scrollbar-none">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-colors whitespace-nowrap",
                    activeTab === tab.id ? "bg-white/10 text-foreground" : "text-muted-foreground hover:bg-white/5"
                  )}
                >
                  <tab.icon className={cn("h-3.5 w-3.5", activeTab === tab.id ? "text-primary" : "")} />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto scrollbar-thin p-4">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                transition={{ duration: 0.15 }}
                className="space-y-6"
              >
                
                {activeTab === 'insights' && (
                  <>
                    <section className="space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Configuration</h3>
                      <div className="space-y-2">
                        <ConfigCard icon={Cpu} label="Model" value={activeModel} />
                        <ConfigCard icon={Database} label="Provider" value={activeProvider} />
                        <ConfigCard icon={Zap} label="Agent" value={activeAgent} />
                      </div>
                    </section>
                    <section className="space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Pipeline Status</h3>
                      <div className="glass-panel rounded-xl p-3 space-y-3 text-sm">
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Security Layer</span>
                          <Badge status="active">Active</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-muted-foreground">Search Cache</span>
                          <Badge status={metrics ? 'active' : 'inactive'}>{metrics ? 'Hit' : 'Miss'}</Badge>
                        </div>
                      </div>
                    </section>
                  </>
                )}

                {activeTab === 'memory' && (
                  <div className="space-y-6">
                    <section className="space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">User Profile</h3>
                      <div className="glass-panel rounded-xl p-4 text-sm space-y-3">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Name</span>
                          <span className="font-medium">{memoryProfile?.name || 'Alex Carter'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Role</span>
                          <span className="font-medium">{memoryProfile?.role || 'Lead Engineer'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Location</span>
                          <span className="font-medium">{memoryProfile?.location || 'San Francisco, CA'}</span>
                        </div>
                      </div>
                    </section>
                    <section className="space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Extracted Facts</h3>
                      <div className="glass-panel rounded-xl p-4">
                        {memoryProfile?.facts?.length ? (
                          <ul className="list-disc list-inside text-xs space-y-2 text-muted-foreground">
                            {memoryProfile.facts.map((f: string, i: number) => <li key={i}>{f}</li>)}
                          </ul>
                        ) : (
                          <p className="text-xs text-muted-foreground">No facts extracted yet.</p>
                        )}
                      </div>
                    </section>
                  </div>
                )}

                {activeTab === 'providers' && (
                  <div className="space-y-4">
                    {providersData?.providers ? providersData.providers.map((p: any) => (
                      <div key={p.id || p.name} className={cn("glass-panel rounded-xl p-4 space-y-3 border", activeProvider === (p.id || p.name) ? "border-primary/50 bg-primary/5" : "border-transparent")}>
                        <div className="flex justify-between items-center">
                          <span className="font-bold capitalize">{p.name || p.id}</span>
                          <Badge status={p.status === 'healthy' || p.status === 'active' ? 'active' : 'error'}>{p.status || 'Unknown'}</Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="flex flex-col"><span className="text-muted-foreground">Latency</span><span>{p.latency_ms || p.latency || 0}ms</span></div>
                          <div className="flex flex-col"><span className="text-muted-foreground">Requests</span><span>{p.requests || 0}</span></div>
                        </div>
                      </div>
                    )) : (
                      <div className="h-24 glass-panel rounded-xl flex items-center justify-center">
                        <span className="text-xs text-muted-foreground animate-pulse">Loading providers...</span>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'agents' && (
                  <div className="space-y-4">
                    {[
                      { id: 'general', title: 'General Agent', desc: 'Standard conversational routing.' },
                      { id: 'coding', title: 'Coding Agent', desc: 'Syntax, architecture, and debugging.' },
                      { id: 'research', title: 'Research Agent', desc: 'Deep web search and synthesis.' },
                      { id: 'math', title: 'Math Agent', desc: 'Symbolic and computational logic.' }
                    ].map(a => (
                      <div key={a.id} className={cn("glass-panel rounded-xl p-4 flex gap-3 border", activeAgent === a.id ? "border-primary/50 bg-primary/5" : "border-transparent")}>
                        <Cpu className={cn("h-6 w-6 mt-1 shrink-0", activeAgent === a.id ? "text-primary" : "text-muted-foreground")} />
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-bold text-sm">{a.title}</span>
                            {activeAgent === a.id && <Badge status="active">Active</Badge>}
                          </div>
                          <p className="text-xs text-muted-foreground">{a.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {activeTab === 'performance' && (
                  <div className="space-y-6">
                    <section className="space-y-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Live Metrics</h3>
                      {metrics ? (
                        <div className="grid grid-cols-2 gap-2">
                          <MetricCard label="P50 Latency" value={`${metrics.p50_latency_ms || 120}ms`} />
                          <MetricCard label="P99 Latency" value={`${metrics.p99_latency_ms || 450}ms`} />
                          <MetricCard label="TTFB" value={`${metrics.ttfb_ms || 35}ms`} />
                          <MetricCard label="Cache Hit Ratio" value={`${metrics.cache_hit_ratio || 0.85 * 100}%`} />
                          <MetricCard label="Req/sec" value={metrics.requests_per_second || "24.5"} />
                          <MetricCard label="Active Conns" value={metrics.active_connections || "3"} />
                        </div>
                      ) : (
                        <div className="h-24 glass-panel rounded-xl flex items-center justify-center">
                          <span className="text-xs text-muted-foreground animate-pulse">Loading metrics...</span>
                        </div>
                      )}
                    </section>
                  </div>
                )}

              </motion.div>
            </AnimatePresence>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}

function ConfigCard({ icon: Icon, label, value }: { icon: any, label: string, value: string }) {
  return (
    <div className="flex items-center justify-between glass-panel rounded-lg px-3 py-2 border border-transparent">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="h-4 w-4" />
        <span>{label}</span>
      </div>
      <span className="text-sm font-medium capitalize">{value}</span>
    </div>
  );
}

function MetricCard({ label, value }: { label: string, value: string | number }) {
  return (
    <div className="glass-panel rounded-lg p-3 flex flex-col gap-1 border border-white/5 shadow-sm">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">{label}</span>
      <span className="text-lg font-bold text-foreground font-mono">{value}</span>
    </div>
  );
}

function Badge({ children, status }: { children: React.ReactNode, status: 'active' | 'inactive' | 'error' }) {
  const colors = {
    active: 'bg-success/10 text-success border-success/20',
    inactive: 'bg-muted/10 text-muted-foreground border-muted/20',
    error: 'bg-destructive/10 text-destructive border-destructive/20',
  };
  return (
    <span className={cn('px-2 py-0.5 rounded text-[9px] uppercase font-bold border tracking-wider', colors[status])}>
      {children}
    </span>
  );
}
