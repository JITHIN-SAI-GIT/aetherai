import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface KeysState {
  keys: Record<string, string>;
  setKey: (provider: string, key: string) => void;
  removeKey: (provider: string) => void;
}

export const useKeysStore = create<KeysState>()(
  persist(
    (set) => ({
      keys: {},
      setKey: (provider, key) => set((state) => ({ keys: { ...state.keys, [provider]: key } })),
      removeKey: (provider) => set((state) => {
        const newKeys = { ...state.keys };
        delete newKeys[provider];
        return { keys: newKeys };
      }),
    }),
    {
      name: 'aether-api-keys',
      // Store in sessionStorage so keys don't persist across browser tabs/restarts
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
