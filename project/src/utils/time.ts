export function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = now - timestamp;
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 7) return new Date(timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' });
  if (days >= 1) return `${days}d ago`;
  if (hours >= 1) return `${hours}h ago`;
  if (minutes >= 1) return `${minutes}m ago`;
  return 'just now';
}

export function getGreeting(): { greeting: string; emoji: string } {
  const hour = new Date().getHours();
  if (hour < 12) return { greeting: 'Good Morning', emoji: '☀️' };
  if (hour < 18) return { greeting: 'Good Afternoon', emoji: '🌤️' };
  return { greeting: 'Good Evening', emoji: '🌙' };
}

export function groupByDate<T extends { updatedAt: number }>(items: T[]): Record<string, T[]> {
  const groups: Record<string, T[]> = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86400000;
  const weekAgo = today - 7 * 86400000;

  for (const item of items) {
    let key: string;
    if (item.updatedAt >= today) key = 'Today';
    else if (item.updatedAt >= yesterday) key = 'Yesterday';
    else if (item.updatedAt >= weekAgo) key = 'Previous 7 days';
    else key = 'Older';

    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  }
  return groups;
}
