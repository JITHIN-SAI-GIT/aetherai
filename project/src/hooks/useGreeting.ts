import { useEffect, useState } from 'react';
import { getGreeting } from '@/utils/time';

export function useGreeting() {
  const [greeting, setGreeting] = useState(() => getGreeting());

  useEffect(() => {
    const interval = setInterval(() => {
      setGreeting(getGreeting());
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  return greeting;
}
