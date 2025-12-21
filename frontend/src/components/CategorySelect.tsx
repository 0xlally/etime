import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { Category } from '../types';

interface CategorySelectProps {
  value?: number;
  onChange: (categoryId: number | undefined) => void;
  disabled?: boolean;
  label?: string;
  allowEmpty?: boolean; // 是否允许空值（用于“全部分类”等场景）
  showCreate?: boolean; // 是否显示创建分类表单
}

export const CategorySelect: React.FC<CategorySelectProps> = ({
  value,
  onChange,
  disabled,
  label = '选择分类',
  allowEmpty = false,
  showCreate = true,
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newColor, setNewColor] = useState('#3498db');

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

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) {
      alert('请输入分类名称');
      return;
    }
    try {
      setCreating(true);
      const payload: any = { name: newName.trim() };
      if (newColor) {
        payload.color = newColor;
      }
      const created = await apiClient.post<Category>('/categories', payload);
      setNewName('');
      await loadCategories();
      onChange(created.id);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '创建分类失败');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="category-select">
      <label>{label}</label>
      <select
        value={value !== undefined ? String(value) : ''}
        onChange={(e) => {
          const selected = e.target.value;
          const id = selected ? Number(selected) : undefined;
          onChange(id);
        }}
        disabled={disabled || loading}
        required={!allowEmpty}
      >
        <option value="">{allowEmpty ? '全部分类' : '-- 请选择 --'}</option>
        {categories.map((cat) => (
          <option key={cat.id} value={cat.id}>
            {cat.name}
          </option>
        ))}
      </select>

      {showCreate && (
        <form onSubmit={handleCreateCategory} className="category-create-form">
          <div className="form-group">
            <label>新建分类</label>
            <input
              type="text"
              placeholder="分类名称"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>颜色</label>
            <input
              type="color"
              value={newColor}
              onChange={(e) => setNewColor(e.target.value)}
            />
          </div>
          <button type="submit" disabled={creating}>
            {creating ? '创建中...' : '新增分类'}
          </button>
        </form>
      )}
    </div>
  );
};
