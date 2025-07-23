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

export const projectAPI = {
  create: async (data: ProjectCreate) => {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },
  
  get: async (projectId: string) => {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
    return response.json();
  },
  
  getStatus: async (projectId: string) => {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/status`);
    return response.json();
  },
};

export const generationAPI = {
  process: async (projectId: string, voiceActorId?: string) => {
    const params = new URLSearchParams({
      project_id: projectId,
      ...(voiceActorId && { voice_actor_id: voiceActorId })
    });
    
    const response = await fetch(`${API_BASE_URL}/generate/process?${params}`, {
      method: 'POST',
    });
    return response.json();
  },
  
  getScenarios: async () => {
    const response = await fetch(`${API_BASE_URL}/generate/scenarios`);
    const data = await response.json();
    return data.scenarios || [];
  },
  
  getVoiceActors: async () => {
    const response = await fetch(`${API_BASE_URL}/generate/voice-actors`);
    const data = await response.json();
    return data.voice_actors || [];
  },
  
  download: (projectId: string, fileType: string) => {
    return `${API_BASE_URL}/generate/download/${projectId}/${fileType}`;
  },
}; 