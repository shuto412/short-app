/**
 * シーン編集ダイアログコンポーネント
 */
import React, { useState, useEffect } from 'react';
import { EditableScene, EditableVoiceSettings } from '../../types';
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
    voice_settings: { ...scene.voice_settings }
  });

  useEffect(() => {
    if (open) {
      setFormData({
        text: scene.text,
        scene_type: scene.scene_type,
        duration: scene.duration,
        voice_settings: { ...scene.voice_settings }
      });
    }
  }, [scene, open]);

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: Partial<EditableScene>) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleVoiceSettingChange = (field: keyof EditableVoiceSettings, value: number | string) => {
    setFormData((prev: Partial<EditableScene>) => ({
      ...prev,
      voice_settings: {
        ...prev.voice_settings!,
        [field]: value
      }
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

          {/* 音声設定 */}
          <div className="voice-settings-section">
            <h4>音声設定</h4>
            
            {/* 感情 */}
            <div className="form-group">
              <label htmlFor="emotion">感情</label>
              <select
                id="emotion"
                value={formData.voice_settings?.emotion || 'cheerful'}
                onChange={(e) => handleVoiceSettingChange('emotion', e.target.value)}
              >
                <option value="cheerful">明るい</option>
                <option value="confident">自信に満ちた</option>
                <option value="calm">落ち着いた</option>
                <option value="excited">興奮した</option>
                <option value="serious">真剣な</option>
              </select>
            </div>

            {/* 速度 */}
            <div className="form-group">
              <label htmlFor="speed">速度 (0.5 - 2.0)</label>
              <input
                type="range"
                id="speed"
                min="0.5"
                max="2.0"
                step="0.1"
                value={formData.voice_settings?.speed || 1.0}
                onChange={(e) => handleVoiceSettingChange('speed', parseFloat(e.target.value))}
              />
              <span className="range-value">{formData.voice_settings?.speed || 1.0}x</span>
            </div>

            {/* ピッチ */}
            <div className="form-group">
              <label htmlFor="pitch">ピッチ (0.5 - 2.0)</label>
              <input
                type="range"
                id="pitch"
                min="0.5"
                max="2.0"
                step="0.1"
                value={formData.voice_settings?.pitch || 1.0}
                onChange={(e) => handleVoiceSettingChange('pitch', parseFloat(e.target.value))}
              />
              <span className="range-value">{formData.voice_settings?.pitch || 1.0}x</span>
            </div>

            {/* 音量 */}
            <div className="form-group">
              <label htmlFor="volume">音量 (0.0 - 2.0)</label>
              <input
                type="range"
                id="volume"
                min="0.0"
                max="2.0"
                step="0.1"
                value={formData.voice_settings?.volume || 1.0}
                onChange={(e) => handleVoiceSettingChange('volume', parseFloat(e.target.value))}
              />
              <span className="range-value">{formData.voice_settings?.volume || 1.0}x</span>
            </div>

            {/* ポーズ長 */}
            <div className="form-group">
              <label htmlFor="pause-length">ポーズ長 (0.0 - 2.0秒)</label>
              <input
                type="range"
                id="pause-length"
                min="0.0"
                max="2.0"
                step="0.1"
                              value={formData.voice_settings?.pauseLength || 0.8}
              onChange={(e) => handleVoiceSettingChange('pauseLength', parseFloat(e.target.value))}
            />
            <span className="range-value">{formData.voice_settings?.pauseLength || 0.8}秒</span>
            </div>
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