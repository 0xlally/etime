import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { Category } from '../types';

interface CategorySelectProps {
  value?: number;
  onChange: (categoryId: number) => void;
  disabled?: boolean;
}

export const CategorySelect: React.FC<CategorySelectProps> = ({ value, onChange, disabled }) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const data = await apiClient.get<Category[]>('/categories');
      setCategories(data);
    } catch (error) {
      console.error('加载分类失败', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="category-select">
      <label>选择分类</label>
      <select
        value={value || ''}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={disabled || loading}
        required
      >
        <option value="">-- 请选择 --</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            <span style={{ color: cat.color }}>●</span> {cat.name}
          </option>
        ))}
      </select>
    </div>
  );
};
