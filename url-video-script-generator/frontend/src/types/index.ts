// API関連の型定義
export interface ProjectCreate {
  url: string;
  scenario_type: string;
  options?: {
    target_duration?: number;
    voice_type?: string;
  };
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

export interface VoiceActorSelectorProps {
  voiceActors: VoiceActor[];
  selectedVoiceActorId?: string;
  selectedSpeed?: number;
  onSelect: (voiceActorId: string) => void;
  onSpeedChange?: (speed: number) => void;
  onNext?: () => void;
  isLoading?: boolean;
}

export interface GeneratedFile {
  name: string;
  type: string;
  downloadUrl: string;
}

export interface AudioSegment {
  segment_id: string;
  filename: string;
  text: string;
  duration: number;
  size_bytes: number;
  exists: boolean;
  download_url: string;
  error?: string;
}

export interface AudioFilesResponse {
  project_id: string;
  audio_files: AudioSegment[];
  total_files: number;
  combined_audio_url: string;
}

// 処理ステップの型定義
export interface ProcessingStep {
  step: string;  // ステップ名
  completed: boolean;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file?: string;  // 生成されたファイル名
  startTime?: string;
  endTime?: string;
  error?: string;
}

// 処理状況の型定義
export interface ProcessingStatus {
  project_id: string;
  status: 'created' | 'processing' | 'completed' | 'failed';
  progress: {
    current_step: string;
    total_steps: number;
    completed_steps: number;
    percentage: number;
    steps: ProcessingStep[];
  };
  files: string[];
  created_at?: string;
  updated_at?: string;
  last_updated?: string;  // 最終更新時刻
}

// コンポーネントの型定義
export interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading?: boolean;
  error?: string;
}

export interface ScenarioSelectorProps {
  scenarios: Scenario[];
  selectedScenario?: string;
  onSelect: (scenarioType: string) => void;
  isLoading?: boolean;
}

export interface VoiceActorSelectorProps {
  voiceActors: VoiceActor[];
  selectedVoiceActorId?: string;
  onSelect: (voiceActorId: string) => void;
  onNext?: () => void;
  isLoading?: boolean;
}

export interface ProgressDisplayProps {
  status: ProcessingStatus | null;
  isVisible: boolean;
}

export interface ResultViewerProps {
  projectId: string;
  project: Project;
  files: GeneratedFile[];
  onStartNew: () => void;
}

// アプリケーションの状態管理
export type AppState = 
  | 'url-input'
  | 'scenario-selection'
  | 'voice-actor-selection'
  | 'processing'
  | 'result'; 