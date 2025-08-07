/**
 * 台本編集状態管理フック
 */
import { useState, useCallback } from 'react';
import { EditableScript, EditableScene, SceneUpdateRequest, SceneAddRequest } from '../types';
import scriptEditApi from '../services/scriptEditApi';

interface UseScriptEditorProps {
  projectId: string;
  initialScript?: EditableScript;
}

interface UseScriptEditorReturn {
  script: EditableScript | null;
  isLoading: boolean;
  error: string | null;
  isEdited: boolean;
  
  // 基本操作
  loadScript: () => Promise<void>;
  saveScript: () => Promise<void>;
  
  // シーン操作
  updateScene: (sceneId: number, updates: Partial<EditableScene>) => Promise<void>;
  addScene: (sceneData: SceneAddRequest) => Promise<void>;
  deleteScene: (sceneId: number) => Promise<void>;
  reorderScenes: (sceneOrder: number[]) => Promise<void>;
  
  // 状態管理
  setScript: (script: EditableScript) => void;
  clearError: () => void;
}

export const useScriptEditor = ({ projectId, initialScript }: UseScriptEditorProps): UseScriptEditorReturn => {
  const [script, setScriptState] = useState<EditableScript | null>(initialScript || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEdited, setIsEdited] = useState(false);

  // エラーをクリア
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // スクリプトを設定
  const setScript = useCallback((newScript: EditableScript) => {
    setScriptState(newScript);
    setIsEdited(true);
  }, []);

  // スクリプトを読み込み
  const loadScript = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await scriptEditApi.getScript(projectId);
      
      if (response.success && response.script) {
        setScriptState(response.script);
        setIsEdited(false);
      } else {
        setError(response.message || 'スクリプトの読み込みに失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'スクリプトの読み込みに失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  // スクリプトを保存
  const saveScript = useCallback(async () => {
    if (!script || !projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await scriptEditApi.updateScript(projectId, script);
      
      if (response.success) {
        setIsEdited(false);
      } else {
        setError(response.message || 'スクリプトの保存に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'スクリプトの保存に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [script, projectId]);

  // シーンを更新
  const updateScene = useCallback(async (sceneId: number, updates: Partial<EditableScene>) => {
    if (!script || !projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      // ローカルでシーンを更新
      const updatedScenes = script.scenes.map((scene: EditableScene) => 
        scene.scene_id === sceneId 
          ? { ...scene, ...updates, is_edited: true }
          : scene
      );

      const updatedScript = {
        ...script,
        scenes: updatedScenes,
        metadata: {
          ...script.metadata,
          edited: true
        }
      };

      setScriptState(updatedScript);
      setIsEdited(true);

      // APIでシーンを更新
      const updateRequest: SceneUpdateRequest = {
        ...(updates.text !== undefined && { text: updates.text }),
        ...(updates.voice_settings !== undefined && { voice_settings: updates.voice_settings }),
        ...(updates.duration !== undefined && { duration: updates.duration }),
        ...(updates.scene_type !== undefined && { scene_type: updates.scene_type })
      };

      const response = await scriptEditApi.updateScene(projectId, sceneId, updateRequest);
      
      if (!response.success) {
        setError(response.message || 'シーンの更新に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'シーンの更新に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [script, projectId]);

  // シーンを追加
  const addScene = useCallback(async (sceneData: SceneAddRequest) => {
    if (!script || !projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await scriptEditApi.addScene(projectId, sceneData);
      
      if (response.success && response.scene) {
        const newScene = response.scene as EditableScene;
        const updatedScenes = [...script.scenes, newScene];
        
        const updatedScript = {
          ...script,
          scenes: updatedScenes,
          metadata: {
            ...script.metadata,
            edited: true
          }
        };

        setScriptState(updatedScript);
        setIsEdited(true);
      } else {
        setError(response.message || 'シーンの追加に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'シーンの追加に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [script, projectId]);

  // シーンを削除
  const deleteScene = useCallback(async (sceneId: number) => {
    if (!script || !projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await scriptEditApi.deleteScene(projectId, sceneId);
      
      if (response.success) {
        const updatedScenes = script.scenes.filter((scene: EditableScene) => scene.scene_id !== sceneId);
        
        const updatedScript = {
          ...script,
          scenes: updatedScenes,
          metadata: {
            ...script.metadata,
            edited: true
          }
        };

        setScriptState(updatedScript);
        setIsEdited(true);
      } else {
        setError(response.message || 'シーンの削除に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'シーンの削除に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [script, projectId]);

  // シーン順序を変更
  const reorderScenes = useCallback(async (sceneOrder: number[]) => {
    if (!script || !projectId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await scriptEditApi.reorderScenes(projectId, sceneOrder);
      
      if (response.success) {
        // 新しい順序でシーンを並び替え
        const sceneDict = script.scenes.reduce((acc: Record<number, EditableScene>, scene: EditableScene) => {
          acc[scene.scene_id] = scene;
          return acc;
        }, {} as Record<number, EditableScene>);

        const updatedScenes = sceneOrder.map(sceneId => sceneDict[sceneId]);
        
        const updatedScript = {
          ...script,
          scenes: updatedScenes,
          metadata: {
            ...script.metadata,
            edited: true
          }
        };

        setScriptState(updatedScript);
        setIsEdited(true);
      } else {
        setError(response.message || 'シーンの順序変更に失敗しました');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'シーンの順序変更に失敗しました');
    } finally {
      setIsLoading(false);
    }
  }, [script, projectId]);

  return {
    script,
    isLoading,
    error,
    isEdited,
    loadScript,
    saveScript,
    updateScene,
    addScene,
    deleteScene,
    reorderScenes,
    setScript,
    clearError,
  };
}; 