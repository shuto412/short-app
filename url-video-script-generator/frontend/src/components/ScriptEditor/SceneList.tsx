/**
 * シーン一覧コンポーネント
 */
import React, { useState } from 'react';
import { SceneListProps, EditableScene } from '../../types';
import SceneItem from './SceneItem';
import SceneEditDialog from './SceneEditDialog';
import './SceneList.css';

const SceneList: React.FC<SceneListProps> = ({
  scenes,
  onSceneUpdate,
  onSceneDelete,
  onSceneAdd,
  onSceneReorder
}) => {
  const [editingScene, setEditingScene] = useState<EditableScene | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  const handleEditScene = (scene: EditableScene) => {
    setEditingScene(scene);
    setIsEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setIsEditDialogOpen(false);
    setEditingScene(null);
  };

  const handleSaveScene = (updates: Partial<EditableScene>) => {
    if (editingScene) {
      onSceneUpdate(editingScene.scene_id, updates);
      handleCloseEditDialog();
    }
  };

  const handleDeleteScene = (sceneId: number) => {
    if (window.confirm('このシーンを削除しますか？')) {
      onSceneDelete(sceneId);
    }
  };

  const handleAddScene = () => {
    // 新しいシーンを追加
    onSceneAdd();
  };

  const getSceneTypeLabel = (sceneType: string): string => {
    const typeLabels: Record<string, string> = {
      'opening': 'オープニング',
      'main_content': 'メインコンテンツ',
      'explanation': '説明',
      'demonstration': 'デモンストレーション',
      'conclusion': '結論',
      'cta': 'CTA'
    };
    return typeLabels[sceneType] || sceneType;
  };

  return (
    <div className="scene-list">
      <div className="scene-list-header">
        <h3>シーン一覧 ({scenes.length}件)</h3>
        <button 
          className="btn btn-primary"
          onClick={handleAddScene}
        >
          + シーン追加
        </button>
      </div>

      <div className="scene-list-content">
        {scenes.length === 0 ? (
          <div className="empty-state">
            <p>シーンがありません</p>
            <button 
              className="btn btn-primary"
              onClick={handleAddScene}
            >
              最初のシーンを追加
            </button>
          </div>
        ) : (
          <div className="scene-items">
            {scenes.map((scene, index) => (
              <SceneItem
                key={scene.scene_id}
                scene={scene}
                sceneIndex={index}
                sceneTypeLabel={getSceneTypeLabel(scene.scene_type)}
                onUpdate={(updates) => onSceneUpdate(scene.scene_id, updates)}
                onDelete={() => handleDeleteScene(scene.scene_id)}
                onEdit={() => handleEditScene(scene)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 編集ダイアログ */}
      {editingScene && (
        <SceneEditDialog
          scene={editingScene}
          open={isEditDialogOpen}
          onClose={handleCloseEditDialog}
          onSave={handleSaveScene}
        />
      )}
    </div>
  );
};

export default SceneList; 