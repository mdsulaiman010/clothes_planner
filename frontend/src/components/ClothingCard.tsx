import { WardrobeItem } from '../api/wardrobe';

interface Props {
  item: WardrobeItem;
  selected: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function ClothingCard({ item, selected, onSelect, onDelete }: Props) {
  return (
    <div className={`clothing-card ${selected ? 'selected' : ''}`} onClick={() => onSelect(item.id)}>
      <img src={item.url} alt={item.subCategory || 'clothing'} loading="lazy" />
      <div className="card-overlay">
        <span className="card-label">{item.subCategory}</span>
        <button
          className="card-delete"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(item.id);
          }}
          title="Delete"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
