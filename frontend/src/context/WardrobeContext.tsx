import { createContext, useContext, useState, ReactNode } from 'react';

interface WardrobeState {
  selectedItems: string[];
  toggleItem: (id: string) => void;
  clearSelection: () => void;
}

const WardrobeContext = createContext<WardrobeState>(null!);

export function WardrobeProvider({ children }: { children: ReactNode }) {
  const [selectedItems, setSelectedItems] = useState<string[]>([]);

  function toggleItem(id: string) {
    setSelectedItems((prev) => (prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]));
  }

  function clearSelection() {
    setSelectedItems([]);
  }

  return (
    <WardrobeContext.Provider value={{ selectedItems, toggleItem, clearSelection }}>
      {children}
    </WardrobeContext.Provider>
  );
}

export function useWardrobe() {
  return useContext(WardrobeContext);
}
