/**
 * シーン編集ダイアログコンポーネント
 */
import React, { useState, useEffect } from 'react';
import { EditableScene } from '../../types';
import './SceneEditDialog.css';

interface SceneEditDialogProps {
  scene: EditableScene;
  open: boolean;
  onClose: () => void;
  onSave: (updates: Partial<EditableScene>) => void;
}

const SceneEditDialog: React.FC<SceneEditDialogProps> = ({
  scene,
  open,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = useState<Partial<EditableScene>>({
    text: scene.text,
    scene_type: scene.scene_type,
    duration: scene.duration,
  });

  useEffect(() => {
    if (open) {
      setFormData({
        text: scene.text,
        scene_type: scene.scene_type,
        duration: scene.duration,
      });
    }
  }, [scene, open]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: Partial<EditableScene>) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = () => {
    onSave(formData);
  };

  const handleCancel = () => {
    onClose();
  };

  if (!open) return null;

  return (
    <div className="dialog-overlay">
      <div className="dialog-content">
        <div className="dialog-header">
          <h3>シーン {scene.scene_id} を編集</h3>
          <button className="dialog-close" onClick={handleCancel}>
            ×
          </button>
        </div>

        <div className="dialog-body">
          {/* シーンタイプ */}
          <div className="form-group">
            <label htmlFor="scene-type">シーンタイプ</label>
            <select
              id="scene-type"
              value={formData.scene_type || ''}
              onChange={(e) => handleInputChange('scene_type', e.target.value)}
            >
              <option value="opening">オープニング</option>
              <option value="main_content">メインコンテンツ</option>
              <option value="explanation">説明</option>
              <option value="demonstration">デモンストレーション</option>
              <option value="conclusion">結論</option>
              <option value="cta">CTA</option>
            </select>
          </div>

          {/* 時間 */}
          <div className="form-group">
            <label htmlFor="duration">時間 (秒)</label>
            <input
              type="number"
              id="duration"
              min="0.1"
              step="0.1"
              value={formData.duration || 0}
              onChange={(e) => handleInputChange('duration', parseFloat(e.target.value))}
            />
          </div>

          {/* テキスト */}
          <div className="form-group">
            <label htmlFor="text">テキスト</label>
            <textarea
              id="text"
              rows={6}
              value={formData.text || ''}
              onChange={(e) => handleInputChange('text', e.target.value)}
              placeholder="シーンのテキストを入力してください"
            />
          </div>
        </div>

        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={handleCancel}>
            キャンセル
          </button>
          <button className="btn btn-primary" onClick={handleSave}>
            保存
          </button>
        </div>
      </div>
    </div>
  );
};

export default SceneEditDialog; 