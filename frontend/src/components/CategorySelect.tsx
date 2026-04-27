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
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');
  const [editColor, setEditColor] = useState('#3498db');
  const [saving, setSaving] = useState(false);

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

  const selectedCategory = categories.find((cat) => cat.id === value);

  const startEdit = (category: Category) => {
    setEditingId(category.id);
    setEditName(category.name);
    setEditColor(category.color || '#3498db');
  };

  const handleUpdateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    if (!editName.trim()) {
      alert('请输入分类名称');
      return;
    }

    try {
      setSaving(true);
      const updated = await apiClient.patch<Category>(`/categories/${editingId}`, {
        name: editName.trim(),
        color: editColor,
      });
      setEditingId(null);
      setEditName('');
      setEditColor('#3498db');
      await loadCategories();
      onChange(updated.id);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      alert(typeof detail === 'string' ? detail : '更新分类失败');
    } finally {
      setSaving(false);
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
          setEditingId(null);
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

      {showCreate && selectedCategory && (
        <div className="category-edit-panel">
          {editingId === selectedCategory.id ? (
            <form onSubmit={handleUpdateCategory} className="category-edit-form">
              <div className="form-group">
                <label>分类名称</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label>颜色</label>
                <input
                  type="color"
                  value={editColor}
                  onChange={(e) => setEditColor(e.target.value)}
                />
              </div>
              <div className="category-edit-actions">
                <button type="button" onClick={() => setEditingId(null)} disabled={saving}>
                  取消
                </button>
                <button type="submit" disabled={saving}>
                  {saving ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          ) : (
            <div className="category-current">
              <span
                className="category-color-dot"
                style={{ background: selectedCategory.color || '#999' }}
              />
              <span>{selectedCategory.name}</span>
              <button type="button" onClick={() => startEdit(selectedCategory)}>
                编辑
              </button>
            </div>
          )}
        </div>
      )}

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
