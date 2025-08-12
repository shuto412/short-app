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
    text_jp: scene.text_jp,
    scene_type: scene.scene_type,
    duration: scene.duration,
  });
  const [userEditedDuration, setUserEditedDuration] = useState<boolean>(false);

  const computeEstimatedDuration = (text: string, speed: number): number => {
    const charsPerMinute = 300; // 日本語の平均読み上げ速度
    const charsPerSecond = (charsPerMinute / 60) * (speed || 1.0);
    const length = (text || '').length;
    const rawSeconds = charsPerSecond > 0 ? length / charsPerSecond : length / 5.0;
    const clamped = Math.max(1, Math.min(300, rawSeconds));
    return Math.round(clamped * 10) / 10; // 小数1桁
  };

  useEffect(() => {
    if (open) {
      setFormData({
        text: scene.text,
        text_jp: scene.text_jp,
        scene_type: scene.scene_type,
        duration: scene.duration,
      });
      setUserEditedDuration(false);
    }
  }, [scene, open]);

  // テキスト変更時に、ユーザーが時間を手動編集していない場合のみ自動推定で反映
  useEffect(() => {
    if (!open) return;
    if (userEditedDuration) return;
    const speed = scene.voice_settings?.speed ?? 1.0;
    const estimated = computeEstimatedDuration(formData.text_jp || formData.text || '', speed);
    if (typeof formData.duration !== 'number' || Math.abs(estimated - formData.duration) >= 0.1) {
      setFormData((prev) => ({ ...prev, duration: estimated }));
    }
  }, [open, userEditedDuration, formData.text, scene.voice_settings]);

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
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (!Number.isNaN(val)) {
                  setUserEditedDuration(true);
                  handleInputChange('duration', val);
                }
              }}
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

          {/* 読み（ひらがな） */}
          <div className="form-group">
            <label htmlFor="text_jp">読み（ひらがな）</label>
            <textarea
              id="text_jp"
              rows={6}
              value={formData.text_jp || ''}
              onChange={(e) => handleInputChange('text_jp', e.target.value)}
              placeholder="ひらがなで読みを入力してください"
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