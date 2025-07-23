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

export interface GeneratedFile {
  name: string;
  type: string;
  downloadUrl: string;
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

export interface ProgressDisplayProps {
  status: any;
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
  | 'processing'
  | 'result'; 