/**
 * 個別シーンコンポーネント
 */
import React from 'react';
import { EditableScene } from '../../types';
import './SceneItem.css';

interface SceneItemProps {
  scene: EditableScene;
  sceneIndex: number;
  sceneTypeLabel: string;
  onUpdate: (updates: Partial<EditableScene>) => void;
  onDelete: () => void;
  onEdit: () => void;
}

const SceneItem: React.FC<SceneItemProps> = ({
  scene,
  sceneIndex,
  sceneTypeLabel,
  onUpdate,
  onDelete,
  onEdit
}) => {
  const getEmotionLabel = (emotion: string): string => {
    const emotionLabels: Record<string, string> = {
      'cheerful': '明るい',
      'confident': '自信に満ちた',
      'calm': '落ち着いた',
      'excited': '興奮した',
      'serious': '真剣な'
    };
    return emotionLabels[emotion] || emotion;
  };

  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className={`scene-item ${scene.is_edited ? 'scene-item-edited' : ''}`}>
      <div className="scene-item-header">
        <div className="scene-item-info">
          <span className="scene-number">シーン {scene.scene_id}</span>
          <span className="scene-type">{sceneTypeLabel}</span>
          <span className="scene-duration">{scene.duration}秒</span>
          {scene.is_edited && (
            <span className="scene-edited-badge">編集済み</span>
          )}
        </div>
        <div className="scene-item-actions">
          <button 
            className="btn btn-sm btn-primary"
            onClick={onEdit}
            title="編集"
          >
            編集
          </button>
          <button 
            className="btn btn-sm btn-danger"
            onClick={onDelete}
            title="削除"
          >
            削除
          </button>
        </div>
      </div>

      <div className="scene-item-content">
        <div className="scene-text">
          <h4>テキスト</h4>
          <p>{truncateText(scene.text)}</p>
        </div>

        <div className="scene-voice-settings">
          <h4>音声設定</h4>
          <div className="voice-settings-grid">
            <div className="voice-setting-item">
              <span className="setting-label">感情:</span>
              <span className="setting-value">{getEmotionLabel(scene.voice_settings.emotion || 'cheerful')}</span>
            </div>
            <div className="voice-setting-item">
              <span className="setting-label">速度:</span>
              <span className="setting-value">{scene.voice_settings.speed}x</span>
            </div>
            <div className="voice-setting-item">
              <span className="setting-label">ピッチ:</span>
              <span className="setting-value">{scene.voice_settings.pitch}x</span>
            </div>
            <div className="voice-setting-item">
              <span className="setting-label">音量:</span>
              <span className="setting-value">{scene.voice_settings.volume}x</span>
            </div>
            <div className="voice-setting-item">
              <span className="setting-label">ポーズ:</span>
                              <span className="setting-value">{scene.voice_settings.pauseLength}秒</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SceneItem; 