import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { WorkTarget, WorkEvaluation, Category } from '../types';

export const Targets: React.FC = () => {
  const [targets, setTargets] = useState<WorkTarget[]>([]);
  const [evaluations, setEvaluations] = useState<WorkEvaluation[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    target_type: 'daily' as 'daily' | 'weekly' | 'monthly' | 'tomorrow',
    target_seconds: 3600,
    category_ids: [] as number[],
    is_enabled: true,
    effective_from: (() => {
      const now = new Date();
      const iso = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
      return iso; // local YYYY-MM-DDTHH:mm
    })(),
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [targetsData, evaluationsData, categoriesData] = await Promise.all([
        apiClient.get<WorkTarget[]>('/targets'),
        apiClient.get<WorkEvaluation[]>('/evaluations'),
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
      const effective = formData.effective_from.includes(':')
        ? `${formData.effective_from}:00`
        : formData.effective_from;

      const created = await apiClient.post<WorkTarget>('/targets', {
        period: formData.target_type,
        target_seconds: formData.target_seconds,
        include_category_ids: formData.category_ids.length > 0 ? formData.category_ids : null,
        effective_from: effective,
      });
      setTargets((prev) => [created, ...prev]);
      setShowForm(false);
      loadData();
      setFormData({
        target_type: 'daily',
        target_seconds: 3600,
        category_ids: [],
        is_enabled: true,
        effective_from: (() => {
          const now = new Date();
          const iso = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16);
          return iso;
        })(),
      });
      alert('目标创建成功');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (Array.isArray(detail)) {
        alert(detail.map((d: any) => d.msg).join(', '));
      } else {
        alert(typeof detail === 'string' ? detail : '创建失败');
      }
    }
  };

  const toggleTarget = async (id: number, is_active: boolean) => {
    try {
      await apiClient.patch(`/targets/${id}`, { is_active: !is_active });
      alert('目标状态已更新');
      loadData();
    } catch (error: any) {
      alert(error?.response?.data?.detail || '更新失败');
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
                  target_type: e.target.value as 'daily' | 'weekly' | 'monthly' | 'tomorrow',
                })
              }
            >
              <option value="tomorrow">明天</option>
              <option value="daily">每日</option>
              <option value="weekly">每周</option>
              <option value="monthly">每月</option>
            </select>
          </div>


          <div className="form-group">
            <label>生效时间（从此时间开始计算）</label>
            <input
              type="datetime-local"
              step="60"
              value={formData.effective_from}
              onChange={(e) =>
                setFormData({ ...formData, effective_from: e.target.value })
              }
              required
            />
            <small style={{ color: '#666', fontSize: '0.85em' }}>
              {formData.target_type === 'tomorrow' 
                ? '选择"明天"时，建议设置为明天 00:00，此目标将优先于"每日"目标'
                : '例如：设置明天的日目标，选择明天 00:00；设置下周的周目标，选择下周一 00:00'}
            </small>
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
                <th>生效时间</th>
                <th>分类</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((target) => {
                const isActive = target.is_active ?? target.is_enabled ?? true;
                const period = target.period ?? target.target_type ?? 'daily';
                const categoryIds = target.include_category_ids ?? target.category_ids ?? [];
                
                return (
                  <tr key={target.id}>
                    <td>
                      {period === 'tomorrow'
                        ? '明天'
                        : period === 'daily'
                        ? '每日'
                        : period === 'weekly'
                        ? '每周'
                        : '每月'}
                    </td>
                    <td>{formatTime(target.target_seconds)}</td>
                    <td>
                      {target.effective_from 
                        ? new Date(target.effective_from).toLocaleString('zh-CN', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        : '立即生效'}
                    </td>
                    <td>
                      {categoryIds.length > 0
                        ? categoryIds
                            .map((id) => categories.find((c) => c.id === id)?.name)
                            .filter(Boolean)
                            .join(', ') || '全部'
                        : '全部'}
                    </td>
                    <td>{isActive ? '启用' : '停用'}</td>
                    <td>
                      <button onClick={() => toggleTarget(target.id, isActive)}>
                        {isActive ? '停用' : '启用'}
                      </button>
                    </td>
                  </tr>
                );
              })}
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
              {evaluations.slice(0, 10).map((evaluation) => (
                <tr key={evaluation.id}>
                  <td>{evaluation.evaluation_date}</td>
                  <td>
                    {evaluation.target?.target_type === 'tomorrow'
                      ? '明天'
                      : evaluation.target?.target_type === 'daily'
                      ? '每日'
                      : evaluation.target?.target_type === 'weekly'
                      ? '每周'
                      : '每月'}{' '}
                    {formatTime(evaluation.target?.target_seconds || 0)}
                  </td>
                  <td>{formatTime(evaluation.actual_seconds)}</td>
                  <td className={evaluation.is_pass ? 'pass' : 'fail'}>
                    {evaluation.is_pass ? '✓ 达标' : '✗ 未达标'}
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
