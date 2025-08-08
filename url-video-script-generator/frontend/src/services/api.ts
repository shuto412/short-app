const API_BASE_URL = 'http://localhost:8080/api';

export interface ProjectCreate {
  url: string;
  scenario_type: string;
  options?: Record<string, any>;
}

export interface Project {
  id: string;
  url: string;
  title: string;
  scenario_type: string;
  status: 'created' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
}

export interface VoiceActor {
  id: string;
  name: string;
  description?: string;
}

// デバッグ用のfetchラッパー
const debugFetch = async (url: string, options: RequestInit = {}) => {
  console.log('🌐 API Request:', url, options);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    console.log('✅ API Response:', response.status, response.statusText);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('📦 API Data:', data);
    return data;
    
  } catch (error) {
    console.error('❌ API Error:', error);
    console.error('🔧 Debug Info:', {
      url,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    });
    throw error;
  }
};

export const projectAPI = {
  create: async (data: ProjectCreate) => {
    return await debugFetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  
  get: async (projectId: string) => {
    return await debugFetch(`${API_BASE_URL}/projects/${projectId}`);
  },
  
  getStatus: async (projectId: string) => {
    return await debugFetch(`${API_BASE_URL}/projects/${projectId}/status`);
  },
};

export const generationAPI = {
  process: async (projectId: string, voiceActorId?: string, voiceSpeed?: number) => {
    const params = new URLSearchParams({
      project_id: projectId,
      ...(voiceActorId && { voice_actor_id: voiceActorId }),
      ...(voiceSpeed && { voice_speed: voiceSpeed.toString() })
    });
    
    return await debugFetch(`${API_BASE_URL}/generate/process?${params}`, {
      method: 'POST',
    });
  },
  
  getScenarios: async () => {
    console.log('🎬 Getting scenarios...');
    const data = await debugFetch(`${API_BASE_URL}/generate/scenarios`);
    return data.scenarios || [];
  },
  
  getVoiceActors: async () => {
    console.log('🎤 Getting voice actors...');
    const data = await debugFetch(`${API_BASE_URL}/generate/voice-actors`);
    return data.voice_actors || [];
  },
  
  getAudioFiles: async (projectId: string) => {
    console.log(`🎵 Getting audio files for project: ${projectId}`);
    try {
      const data = await debugFetch(`${API_BASE_URL}/audio-files/${projectId}`);
      return data;
    } catch (error) {
      console.error('Failed to get audio files:', error);
      // フォールバック: 統合ファイルのみ
      return {
        project_id: projectId,
        audio_files: [],
        total_files: 0,
        combined_audio_url: `${API_BASE_URL}/generate/download/${projectId}/audio`
      };
    }
  },
  
  download: (projectId: string, fileType: string) => {
    return `${API_BASE_URL}/generate/download/${projectId}/${fileType}`;
  },
  
  downloadAudioSegment: (projectId: string, filename: string) => {
    return `${API_BASE_URL}/generate/download/${projectId}/segments/${filename}`;
  },
}; 

export const stageAPI = {
  startScraping: async (projectId: string) => {
    return await debugFetch(`${API_BASE_URL}/stages/scraping?project_id=${encodeURIComponent(projectId)}`, {
      method: 'POST',
    });
  },

  startSummary: async (projectId: string) => {
    return await debugFetch(`${API_BASE_URL}/stages/summary?project_id=${encodeURIComponent(projectId)}`, {
      method: 'POST',
    });
  },

  startScriptGeneration: async (projectId: string, scenarioType: string) => {
    return await debugFetch(`${API_BASE_URL}/stages/script`, {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, scenario_type: scenarioType }),
    });
  },

  // 音声設定関連（段階APIに合わせたエンドポイント）
  getVoicePrompt: async (projectId: string) => {
    return await debugFetch(`${API_BASE_URL}/stages/voice-settings/${encodeURIComponent(projectId)}`);
  },

  saveVoicePrompt: async (projectId: string, voicePrompt: any) => {
    return await debugFetch(`${API_BASE_URL}/stages/voice-settings/${encodeURIComponent(projectId)}`, {
      method: 'PUT',
      body: JSON.stringify(voicePrompt),
    });
  },

  // サーバ側にバッチエンドポイントがないため、クライアント側で一括適用→PUT
  batchUpdateVoiceParameters: async (projectId: string, parameters: any) => {
    const current = await debugFetch(`${API_BASE_URL}/stages/voice-settings/${encodeURIComponent(projectId)}`);
    if (!current || !current.segments) return current;
    const updated = {
      ...current,
      segments: current.segments.map((seg: any) => ({
        ...seg,
        parameters: { ...seg.parameters, ...parameters },
      })),
    };
    return await debugFetch(`${API_BASE_URL}/stages/voice-settings/${encodeURIComponent(projectId)}`, {
      method: 'PUT',
      body: JSON.stringify(updated),
    });
  },

  // プレビューはサーバ未実装のためダミー応答
  previewVoiceSegment: async (_projectId: string, _segmentId: number) => {
    return Promise.resolve({
      preview_description: 'ローカルプレビュー（ダミー）',
      estimated_duration: 3.0,
    });
  },

  // リセットは現在保存されている設定（ファイル）をGETして返す
  resetVoicePrompt: async (projectId: string) => {
    const current = await debugFetch(`${API_BASE_URL}/stages/voice-settings/${encodeURIComponent(projectId)}`);
    return { voice_prompt: current };
  },
};