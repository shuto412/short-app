import React, { useState, useEffect } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UrlInput } from './components/UrlInput';
import { ScenarioSelector } from './components/ScenarioSelector';
import { VoiceActorSelector } from './components/VoiceActorSelector';
import { ProgressDisplay } from './components/ProgressDisplay';
import { ResultViewer } from './components/ResultViewer';
import { projectAPI, generationAPI } from './services/api';
import type { AppState, Scenario, VoiceActor, Project, GeneratedFile } from './types';

// React Query クライアント設定
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5分
    },
  },
});

// Material-UI テーマ設定
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  // 状態管理
  const [appState, setAppState] = useState<AppState>('url-input');
  const [projectId, setProjectId] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [scenarioType, setScenarioType] = useState<string>('');
  const [selectedVoiceActorId, setSelectedVoiceActorId] = useState<string>('231e0170-0ece-4155-be44-231423062f41');
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [voiceActors, setVoiceActors] = useState<VoiceActor[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<GeneratedFile[]>([]);
  const [processingStatus, setProcessingStatus] = useState<any>(null);
  
  // エラー・ローディング状態
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // 初期化: シナリオとボイスアクターを取得
  useEffect(() => {
    const initializeData = async () => {
      try {
        const [scenariosData, voiceActorsData] = await Promise.all([
          generationAPI.getScenarios(),
          generationAPI.getVoiceActors()
        ]);
        setScenarios(scenariosData);
        setVoiceActors(voiceActorsData);
      } catch (error) {
        console.error('初期化エラー:', error);
        setError('初期化に失敗しました。ページを再読み込みしてください。');
      }
    };

    initializeData();
  }, []);

  // 処理状況の監視
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    if (projectId && appState === 'processing') {
      intervalId = setInterval(async () => {
        try {
          const status = await projectAPI.getStatus(projectId);
          setProcessingStatus(status);

          if (status.status === 'completed') {
            // 処理完了時
            const projectData = await projectAPI.get(projectId);
            setProject(projectData.project);
            
            // ファイル一覧を生成
            const generatedFiles: GeneratedFile[] = projectData.files.map((fileName: string) => {
              const fileType = getFileType(fileName);
              return {
                name: fileName,
                type: fileType,
                downloadUrl: generationAPI.download(projectId, fileType)
              };
            });
            setFiles(generatedFiles);
            setAppState('result');
            
          } else if (status.status === 'failed') {
            // 処理失敗時
            setError('処理中にエラーが発生しました。もう一度お試しください。');
            setAppState('url-input');
          }
        } catch (error) {
          console.error('ステータス取得エラー:', error);
        }
      }, 2000); // 2秒間隔で監視
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [projectId, appState]);

  // ファイル名からファイルタイプを推定
  const getFileType = (fileName: string): string => {
    if (fileName.includes('script')) return 'script';
    if (fileName.includes('audio')) return 'audio';
    if (fileName.includes('subtitle.srt')) return 'subtitle';
    if (fileName.includes('subtitle.vtt')) return 'subtitle-vtt';
    if (fileName.includes('summary')) return 'summary';
    if (fileName.includes('scraped_content')) return 'content';
    if (fileName.includes('voice_prompt')) return 'voice-prompt';
    return 'unknown';
  };

  // イベントハンドラー
  const handleUrlSubmit = async (inputUrl: string) => {
    setIsLoading(true);
    setError('');
    setUrl(inputUrl);
    
    try {
      // プロジェクト作成
      const result = await projectAPI.create({
        url: inputUrl,
        scenario_type: 'product_introduction', // デフォルト
        options: {}
      });
      
      setProjectId(result.project_id);
      setAppState('scenario-selection');
    } catch (error: any) {
      setError(error.message || 'プロジェクトの作成に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleScenarioSelect = (selectedScenarioType: string) => {
    setScenarioType(selectedScenarioType);
    setAppState('voice-actor-selection');
  };

  const handleVoiceActorSelect = (voiceActorId: string) => {
    setSelectedVoiceActorId(voiceActorId);
  };

  const handleStartProcessing = async () => {
    setIsLoading(true);
    setError('');

    try {
      // 処理開始
      await generationAPI.process(projectId, selectedVoiceActorId);
      setAppState('processing');
    } catch (error: any) {
      setError(error.message || '処理の開始に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartNew = () => {
    // 状態をリセットして新しいプロジェクトを開始
    setAppState('url-input');
    setProjectId('');
    setUrl('');
    setScenarioType('');
    setSelectedVoiceActorId('231e0170-0ece-4155-be44-231423062f41');
    setProject(null);
    setFiles([]);
    setProcessingStatus(null);
    setError('');
    setIsLoading(false);
  };

  // レンダリング
  const renderCurrentScreen = () => {
    switch (appState) {
      case 'url-input':
        return (
          <UrlInput
            onSubmit={handleUrlSubmit}
            isLoading={isLoading}
            error={error}
          />
        );

      case 'scenario-selection':
        return (
          <ScenarioSelector
            scenarios={scenarios}
            selectedScenario={scenarioType}
            onSelect={handleScenarioSelect}
            isLoading={isLoading}
          />
        );

      case 'voice-actor-selection':
        return (
          <VoiceActorSelector
            voiceActors={voiceActors}
            selectedVoiceActorId={selectedVoiceActorId}
            onSelect={handleVoiceActorSelect}
            onNext={handleStartProcessing}
            isLoading={isLoading}
          />
        );

      case 'processing':
        return (
          <ProgressDisplay
            status={processingStatus}
            isVisible={true}
          />
        );

      case 'result':
        return project ? (
          <ResultViewer
            projectId={projectId}
            project={project}
            files={files}
            onStartNew={handleStartNew}
          />
        ) : (
          <div>プロジェクトデータの読み込み中...</div>
        );

      default:
        return <div>予期しないエラーが発生しました</div>;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          {renderCurrentScreen()}
        </Container>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
