import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { WorkTarget, WorkEvaluation, Category } from '../types';

export const Targets: React.FC = () => {
  const [targets, setTargets] = useState<WorkTarget[]>([]);
  const [evaluations, setEvaluations] = useState<WorkEvaluation[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    target_type: 'daily' as 'daily' | 'weekly' | 'monthly',
    target_seconds: 3600,
    category_ids: [] as number[],
    is_enabled: true,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [targetsData, evaluationsData, categoriesData] = await Promise.all([
        apiClient.get<WorkTarget[]>('/work-targets'),
        apiClient.get<WorkEvaluation[]>('/work-evaluations'),
        apiClient.get<Category[]>('/categories'),
      ]);
      setTargets(targetsData);
      setEvaluations(evaluationsData);
      setCategories(categoriesData);
    } catch (error) {
      console.error('加载数据失败', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.post('/work-targets', formData);
      setShowForm(false);
      loadData();
      setFormData({
        target_type: 'daily',
        target_seconds: 3600,
        category_ids: [],
        is_enabled: true,
      });
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建失败');
    }
  };

  const toggleTarget = async (id: number, is_enabled: boolean) => {
    try {
      await apiClient.patch(`/work-targets/${id}`, { is_enabled: !is_enabled });
      loadData();
    } catch (error) {
      console.error('更新失败', error);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="targets-page">
      <h1>目标设置</h1>

      <button onClick={() => setShowForm(!showForm)}>
        {showForm ? '取消' : '+ 新建目标'}
      </button>

      {showForm && (
        <form onSubmit={handleSubmit} className="target-form">
          <div className="form-group">
            <label>周期</label>
            <select
              value={formData.target_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  target_type: e.target.value as 'daily' | 'weekly' | 'monthly',
                })
              }
            >
              <option value="daily">每日</option>
              <option value="weekly">每周</option>
              <option value="monthly">每月</option>
            </select>
          </div>

          <div className="form-group">
            <label>目标时长（小时）</label>
            <input
              type="number"
              min="1"
              step="0.5"
              value={formData.target_seconds / 3600}
              onChange={(e) =>
                setFormData({ ...formData, target_seconds: Number(e.target.value) * 3600 })
              }
            />
          </div>

          <div className="form-group">
            <label>包含分类</label>
            <div className="category-checkboxes">
              {categories.map((cat) => (
                <label key={cat.id}>
                  <input
                    type="checkbox"
                    checked={formData.category_ids.includes(cat.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({
                          ...formData,
                          category_ids: [...formData.category_ids, cat.id],
                        });
                      } else {
                        setFormData({
                          ...formData,
                          category_ids: formData.category_ids.filter((id) => id !== cat.id),
                        });
                      }
                    }}
                  />
                  {cat.name}
                </label>
              ))}
            </div>
          </div>

          <button type="submit">创建</button>
        </form>
      )}

      <div className="targets-list">
        <h2>我的目标</h2>
        {targets.length === 0 ? (
          <p>暂无目标</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>周期</th>
                <th>目标时长</th>
                <th>分类</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((target) => (
                <tr key={target.id}>
                  <td>
                    {target.target_type === 'daily'
                      ? '每日'
                      : target.target_type === 'weekly'
                      ? '每周'
                      : '每月'}
                  </td>
                  <td>{formatTime(target.target_seconds)}</td>
                  <td>
                    {target.category_ids
                      .map((id) => categories.find((c) => c.id === id)?.name)
                      .join(', ')}
                  </td>
                  <td>{target.is_enabled ? '启用' : '停用'}</td>
                  <td>
                    <button onClick={() => toggleTarget(target.id, target.is_enabled)}>
                      {target.is_enabled ? '停用' : '启用'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="evaluations-list">
        <h2>最近评估结果</h2>
        {evaluations.length === 0 ? (
          <p>暂无评估记录</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>日期</th>
                <th>目标</th>
                <th>实际时长</th>
                <th>结果</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.slice(0, 10).map((eval) => (
                <tr key={eval.id}>
                  <td>{eval.evaluation_date}</td>
                  <td>
                    {eval.target?.target_type === 'daily'
                      ? '每日'
                      : eval.target?.target_type === 'weekly'
                      ? '每周'
                      : '每月'}{' '}
                    {formatTime(eval.target?.target_seconds || 0)}
                  </td>
                  <td>{formatTime(eval.actual_seconds)}</td>
                  <td className={eval.is_pass ? 'pass' : 'fail'}>
                    {eval.is_pass ? '✓ 达标' : '✗ 未达标'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
