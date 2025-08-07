/**
 * 台本編集APIクライアント
 */
import { 
  EditableScript, 
  ScriptEditResponse, 
  SceneUpdateRequest, 
  SceneAddRequest, 
  SceneReorderRequest 
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

class ScriptEditApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * 編集用台本を取得
   */
  async getScript(projectId: string): Promise<ScriptEditResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get script:', error);
      throw error;
    }
  }

  /**
   * 台本を更新
   */
  async updateScript(projectId: string, script: EditableScript): Promise<ScriptEditResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(script),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to update script:', error);
      throw error;
    }
  }

  /**
   * 個別シーンを更新
   */
  async updateScene(projectId: string, sceneId: number, updates: SceneUpdateRequest): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}/scene/${sceneId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to update scene:', error);
      throw error;
    }
  }

  /**
   * 新しいシーンを追加
   */
  async addScene(projectId: string, sceneData: SceneAddRequest): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}/scene`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(sceneData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to add scene:', error);
      throw error;
    }
  }

  /**
   * シーンを削除
   */
  async deleteScene(projectId: string, sceneId: number): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}/scene/${sceneId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to delete scene:', error);
      throw error;
    }
  }

  /**
   * シーン順序を変更
   */
  async reorderScenes(projectId: string, sceneOrder: number[]): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/script/${projectId}/scenes/reorder`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scene_order: sceneOrder }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to reorder scenes:', error);
      throw error;
    }
  }
}

export const scriptEditApi = new ScriptEditApi();
export default scriptEditApi; 