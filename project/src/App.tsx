import { lazy, Suspense, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AnimatedBackground } from '@/components/layout/AnimatedBackground';
import { Logo } from '@/components/ui/Logo';
import { useUIStore } from '@/store/uiStore';

const AppShell = lazy(() =>
  import('@/components/layout/AppShell').then((m) => ({ default: m.AppShell })),
);

const queryClient = new QueryClient();

function LoadingScreen() {
  return (
    <div className="flex h-screen w-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Logo size="lg" animated />
        <p className="text-sm text-muted-foreground animate-pulse">Loading AETHER AI...</p>
      </div>
    </div>
  );
}

export default function App() {
  const { theme } = useUIStore();

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  return (
    <QueryClientProvider client={queryClient}>
      <AnimatedBackground />
      <Suspense fallback={<LoadingScreen />}>
        <AppShell />
      </Suspense>
      <Toaster position="bottom-right" theme={theme === 'system' ? 'system' : theme} />
    </QueryClientProvider>
  );
}
