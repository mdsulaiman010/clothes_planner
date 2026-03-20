import { useState, useEffect, useCallback } from 'react';
import { getItems, getCategories, deleteItem, WardrobeItem } from '../api/wardrobe';
import { useWardrobe } from '../context/WardrobeContext';
import { useChat } from '../context/ChatContext';
import CategoryFilter from '../components/CategoryFilter';
import ClothingGrid from '../components/ClothingGrid';

const ITEMS_PER_PAGE = 20;

export default function WardrobePage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCategory, setActiveCategory] = useState('top');
  const [items, setItems] = useState<WardrobeItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const { selectedItems, toggleItem } = useWardrobe();
  const { setPageContext } = useChat();

  // Load categories once
  useEffect(() => {
    getCategories().then((data) => setCategories(Object.keys(data)));
  }, []);

  // Update chat context
  useEffect(() => {
    setPageContext((prev: Record<string, unknown>) => ({
      ...prev,
      page: 'wardrobe',
      category: activeCategory,
      selectedItems,
    }));
  }, [activeCategory, selectedItems, setPageContext]);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getItems(activeCategory, page * ITEMS_PER_PAGE, ITEMS_PER_PAGE);
      setItems(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  function handleCategoryChange(cat: string) {
    setActiveCategory(cat);
    setPage(0);
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this item?')) return;
    await deleteItem(id);
    fetchItems();
  }

  const totalPages = Math.max(1, Math.ceil(total / ITEMS_PER_PAGE));

  return (
    <div className="page wardrobe-page">
      <h1>My Wardrobe</h1>

      <CategoryFilter categories={categories} active={activeCategory} onChange={handleCategoryChange} />

      {loading ? (
        <p>Loading...</p>
      ) : (
        <ClothingGrid items={items} selectedItems={selectedItems} onSelect={toggleItem} onDelete={handleDelete} />
      )}

      <div className="pagination">
        <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
          &larr; Previous
        </button>
        <span>
          Page {page + 1} of {totalPages}
        </span>
        <button disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>
          Next &rarr;
        </button>
      </div>
    </div>
  );
}
