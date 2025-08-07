/**
 * 台本編集メインコンポーネント
 */
import React, { useState, useEffect } from 'react';
import { EditableScriptEditorProps, EditableScript, EditableScene } from '../../types';
import SceneList from './SceneList';
import './ScriptEditor.css';

const ScriptEditor: React.FC<EditableScriptEditorProps> = ({
  projectId,
  script: initialScript,
  onSave,
  onNext,
  onBack,
  isLoading = false
}) => {
  const [script, setScript] = useState<EditableScript>(initialScript);
  const [hasChanges, setHasChanges] = useState(false);

  // スクリプトが変更されたかを監視
  useEffect(() => {
    const isChanged = JSON.stringify(script) !== JSON.stringify(initialScript);
    setHasChanges(isChanged);
  }, [script, initialScript]);

  const handleSave = async () => {
    try {
      await onSave(script);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save script:', error);
    }
  };

  const handleSceneUpdate = (sceneId: number, updates: Partial<EditableScene>) => {
    const updatedScenes = script.scenes.map(scene => 
      scene.scene_id === sceneId 
        ? { ...scene, ...updates, is_edited: true }
        : scene
    );
    setScript({ ...script, scenes: updatedScenes });
  };

  const handleSceneDelete = (sceneId: number) => {
    const updatedScenes = script.scenes.filter(scene => scene.scene_id !== sceneId);
    setScript({ ...script, scenes: updatedScenes });
  };

  const handleSceneAdd = () => {
    const newSceneId = Math.max(...script.scenes.map(s => s.scene_id), 0) + 1;
    const newScene: EditableScene = {
      scene_id: newSceneId,
      scene_type: 'main_content',
      duration: 5.0,
      text: '新しいシーンを追加しました。編集してください。',
      voice_settings: {
        emotion: 'cheerful',
        speed: 1.0,
        pitch: 1.0,
        volume: 1.0,
        pause_length: 0.8
      },
      is_edited: true
    };
    setScript({ ...script, scenes: [...script.scenes, newScene] });
  };

  const handleSceneReorder = (sceneOrder: number[]) => {
    const reorderedScenes = sceneOrder.map(id => 
      script.scenes.find(scene => scene.scene_id === id)
    ).filter(Boolean) as EditableScene[];
    setScript({ ...script, scenes: reorderedScenes });
  };

  return (
    <div className="script-editor">
      {/* ヘッダー */}
      <div className="script-editor-header">
        <div className="project-info">
          <h2>{script.metadata.title}</h2>
          <p className="project-details">
            プロジェクトID: {script.metadata.project_id} | 
            シナリオタイプ: {script.metadata.scenario_type} | 
            総時間: {script.metadata.total_duration}秒
          </p>
        </div>
        <div className="header-actions">
          <button 
            className="btn btn-secondary" 
            onClick={onBack}
            disabled={isLoading}
          >
            戻る
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={isLoading}
          >
            {hasChanges ? '保存' : '保存済み'}
          </button>
          {onNext && (
            <button 
              className="btn btn-success" 
              onClick={onNext}
              disabled={isLoading}
            >
              次へ
            </button>
          )}
        </div>
      </div>

      {/* ローディング表示 */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>処理中...</p>
        </div>
      )}

      {/* メインコンテンツ */}
      <div className="script-editor-content">
        <SceneList
          scenes={script.scenes}
          onSceneUpdate={handleSceneUpdate}
          onSceneDelete={handleSceneDelete}
          onSceneAdd={handleSceneAdd}
          onSceneReorder={handleSceneReorder}
        />
      </div>

      {/* フッター */}
      <div className="script-editor-footer">
        <div className="footer-info">
          <span>シーン数: {script.scenes.length}</span>
          <span>編集済み: {script.metadata.edited ? 'はい' : 'いいえ'}</span>
          {script.metadata.last_edited && (
            <span>最終編集: {new Date(script.metadata.last_edited).toLocaleString()}</span>
          )}
        </div>
        <div className="footer-actions">
          <button 
            className="btn btn-secondary" 
            onClick={onBack}
            disabled={isLoading}
          >
            戻る
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={isLoading}
          >
            {hasChanges ? '保存' : '保存済み'}
          </button>
          {onNext && (
            <button 
              className="btn btn-success" 
              onClick={onNext}
              disabled={isLoading}
            >
              次へ
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ScriptEditor; 