import React, { useCallback, useEffect, useState } from 'react';
import { ArrowDown, ArrowUp, Trash2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { Category } from '../types';

interface CategoryManagerProps {
  selectedCategoryId?: number;
  onChange: (categoryId: number | undefined) => void;
  onCategoriesChanged: () => void;
}

export const CategoryManager: React.FC<CategoryManagerProps> = ({
  selectedCategoryId,
  onChange,
  onCategoriesChanged,
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [reordering, setReordering] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const loadCategories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Category[]>('/categories');
      setCategories(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('加载分类失败', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCategories();
  }, [loadCategories]);

  const moveCategory = async (categoryId: number, direction: -1 | 1) => {
    const currentIndex = categories.findIndex((category) => category.id === categoryId);
    const targetIndex = currentIndex + direction;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= categories.length) return;

    const previousCategories = categories;
    const nextCategories = [...categories];
    [nextCategories[currentIndex], nextCategories[targetIndex]] = [
      nextCategories[targetIndex],
      nextCategories[currentIndex],
    ];
    setCategories(nextCategories.map((category, index) => ({ ...category, sort_order: index })));

    try {
      setReordering(true);
      const reordered = await apiClient.post<Category[]>('/categories/reorder', {
        category_ids: nextCategories.map((category) => category.id),
      });
      setCategories(reordered);
      onCategoriesChanged();
    } catch (error: any) {
      setCategories(previousCategories);
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '调整分类顺序失败');
      await loadCategories();
    } finally {
      setReordering(false);
    }
  };

  const deleteCategory = async (category: Category) => {
    if (!window.confirm(`删除分类「${category.name}」？历史计时记录会保留，关联快捷模板将停用。`)) {
      return;
    }

    try {
      setDeletingId(category.id);
      await apiClient.delete(`/categories/${category.id}`);
      setCategories((current) => current.filter((item) => item.id !== category.id));
      if (selectedCategoryId === category.id) {
        onChange(undefined);
      }
      onCategoriesChanged();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '删除分类失败');
      await loadCategories();
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="category-manager">
      {loading ? (
        <p className="category-manager-state">正在加载分类...</p>
      ) : categories.length === 0 ? (
        <p className="category-manager-state">暂无可管理的分类</p>
      ) : (
        <div className="category-manager-list">
          {categories.map((category, index) => (
            <div className="category-manager-row" key={category.id}>
              <div className="category-manager-name">
                <span
                  className="category-color-dot"
                  style={{ background: category.color || '#999999' }}
                />
                <strong>{category.name}</strong>
              </div>
              <button
                type="button"
                className="category-manager-icon-button"
                onClick={() => void moveCategory(category.id, -1)}
                disabled={index === 0 || reordering || deletingId !== null}
                aria-label={`上移${category.name}`}
                title="上移"
              >
                <ArrowUp size={18} aria-hidden="true" />
              </button>
              <button
                type="button"
                className="category-manager-icon-button"
                onClick={() => void moveCategory(category.id, 1)}
                disabled={index === categories.length - 1 || reordering || deletingId !== null}
                aria-label={`下移${category.name}`}
                title="下移"
              >
                <ArrowDown size={18} aria-hidden="true" />
              </button>
              <button
                type="button"
                className="category-manager-icon-button danger"
                onClick={() => void deleteCategory(category)}
                disabled={reordering || deletingId !== null}
                aria-label={`删除${category.name}`}
                title="删除"
              >
                <Trash2 size={18} aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
