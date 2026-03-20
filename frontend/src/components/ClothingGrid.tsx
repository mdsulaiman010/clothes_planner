import { WardrobeItem } from '../api/wardrobe';
import ClothingCard from './ClothingCard';

interface Props {
  items: WardrobeItem[];
  selectedItems: string[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function ClothingGrid({ items, selectedItems, onSelect, onDelete }: Props) {
  if (items.length === 0) {
    return <p className="empty-state">No items found in this category.</p>;
  }

  return (
    <div className="clothing-grid">
      {items.map((item) => (
        <ClothingCard
          key={item.id}
          item={item}
          selected={selectedItems.includes(item.id)}
          onSelect={onSelect}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
