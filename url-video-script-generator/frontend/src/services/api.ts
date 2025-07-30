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
  process: async (projectId: string, voiceActorId?: string) => {
    const params = new URLSearchParams({
      project_id: projectId,
      ...(voiceActorId && { voice_actor_id: voiceActorId })
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