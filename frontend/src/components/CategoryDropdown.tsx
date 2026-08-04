import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, ChevronDown } from 'lucide-react';
import { Category } from '../types';

interface CategoryDropdownProps {
  categories: Category[];
  value?: number;
  onChange: (categoryId: number | undefined) => void;
  disabled?: boolean;
  loading?: boolean;
  allowEmpty?: boolean;
}

interface MenuPosition {
  left: number;
  top?: number;
  bottom?: number;
  width: number;
  maxHeight: number;
}

export const CategoryDropdown: React.FC<CategoryDropdownProps> = ({
  categories,
  value,
  onChange,
  disabled = false,
  loading = false,
  allowEmpty = false,
}) => {
  const [open, setOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState<MenuPosition | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const selectedCategory = categories.find((category) => category.id === value);

  const updateMenuPosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;

    const viewportPadding = 12;
    const gap = 6;
    const rect = trigger.getBoundingClientRect();
    const width = Math.min(Math.max(rect.width, 220), window.innerWidth - viewportPadding * 2);
    const left = Math.min(
      Math.max(viewportPadding, rect.left),
      window.innerWidth - width - viewportPadding,
    );
    const spaceBelow = window.innerHeight - rect.bottom - viewportPadding - gap;
    const spaceAbove = rect.top - viewportPadding - gap;
    const openAbove = spaceBelow < 180 && spaceAbove > spaceBelow;
    const availableSpace = Math.max(120, openAbove ? spaceAbove : spaceBelow);

    setMenuPosition({
      left,
      width,
      maxHeight: Math.min(360, availableSpace),
      ...(openAbove
        ? { bottom: window.innerHeight - rect.top + gap }
        : { top: rect.bottom + gap }),
    });
  }, []);

  useEffect(() => {
    if (!open) return undefined;

    updateMenuPosition();
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!triggerRef.current?.contains(target) && !menuRef.current?.contains(target)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };

    document.addEventListener('mousedown', handleOutsideClick);
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('resize', updateMenuPosition);
    window.addEventListener('scroll', updateMenuPosition, true);
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('resize', updateMenuPosition);
      window.removeEventListener('scroll', updateMenuPosition, true);
    };
  }, [open, updateMenuPosition]);

  const selectCategory = (categoryId: number | undefined) => {
    onChange(categoryId);
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <div className="category-picker">
      <button
        ref={triggerRef}
        type="button"
        className="category-picker-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        disabled={disabled || loading}
        onClick={() => {
          if (!open) updateMenuPosition();
          setOpen((current) => !current);
        }}
      >
        <span className="category-picker-value">
          {selectedCategory && (
            <span
              className="category-color-dot"
              style={{ background: selectedCategory.color || '#999999' }}
            />
          )}
          <span>{loading ? '加载中...' : selectedCategory?.name ?? (allowEmpty ? '全部分类' : '-- 请选择 --')}</span>
        </span>
        <ChevronDown size={18} aria-hidden="true" />
      </button>

      {open && menuPosition && createPortal(
        <div
          ref={menuRef}
          id={menuId}
          role="listbox"
          className="category-picker-menu"
          style={menuPosition}
        >
          <button
            type="button"
            role="option"
            aria-selected={value === undefined}
            className={value === undefined ? 'selected' : undefined}
            onClick={() => selectCategory(undefined)}
          >
            <span>{allowEmpty ? '全部分类' : '-- 请选择 --'}</span>
            {value === undefined && <Check size={17} aria-hidden="true" />}
          </button>
          {categories.map((category) => (
            <button
              key={category.id}
              type="button"
              role="option"
              aria-selected={category.id === value}
              className={category.id === value ? 'selected' : undefined}
              onClick={() => selectCategory(category.id)}
            >
              <span className="category-picker-option-label">
                <span
                  className="category-color-dot"
                  style={{ background: category.color || '#999999' }}
                />
                <span>{category.name}</span>
              </span>
              {category.id === value && <Check size={17} aria-hidden="true" />}
            </button>
          ))}
          {categories.length === 0 && (
            <p className="category-picker-empty">暂无分类</p>
          )}
        </div>,
        document.body,
      )}
    </div>
  );
};
