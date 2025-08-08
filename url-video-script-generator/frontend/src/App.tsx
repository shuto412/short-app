import React, { useState, useEffect } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UrlInput } from './components/UrlInput';
import { ScenarioSelector } from './components/ScenarioSelector';
import { VoiceActorSelector } from './components/VoiceActorSelector';
import { ProgressDisplay } from './components/ProgressDisplay';
import { ResultViewer } from './components/ResultViewer';
import { projectAPI, generationAPI, stageAPI } from './services/api';
import ScriptEditor from './components/ScriptEditor/ScriptEditor';
import { EditableScript } from './types';
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
  const [voiceSpeed, setVoiceSpeed] = useState<number>(1.5);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [voiceActors, setVoiceActors] = useState<VoiceActor[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [editableScript, setEditableScript] = useState<EditableScript | null>(null);
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

  const handleVoiceSpeedChange = (speed: number) => {
    setVoiceSpeed(speed);
  };

  const handleStartProcessing = async () => {
    setIsLoading(true);
    setError('');

    try {
      // ユーティリティ: 指定ファイルが生成されるまでポーリング
      const waitForFile = async (targetFile: string, timeoutMs = 120000, intervalMs = 1500) => {
        const start = Date.now();
        for (;;) {
          const status = await projectAPI.getStatus(projectId);
          const files: string[] = status.files || [];
          if (files.includes(targetFile)) return;
          if (Date.now() - start > timeoutMs) throw new Error(`タイムアウト: ${targetFile} の生成を待機中に時間切れ`);
          await new Promise((r) => setTimeout(r, intervalMs));
        }
      };

      // 段階1: スクレイピング → scraped_content.txt を待つ
      await stageAPI.startScraping(projectId);
      await waitForFile('scraped_content.txt');

      // 段階2: 要約 → summary.txt を待つ
      await stageAPI.startSummary(projectId);
      await waitForFile('summary.txt');

      // 段階3: 台本生成 → script.yaml を待つ
      await stageAPI.startScriptGeneration(projectId, scenarioType || 'product_introduction');
      await waitForFile('script.yaml');

      // 台本編集画面へ
      const apiBase = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';
      const scriptResp = await (await fetch(`${apiBase}/api/script/${projectId}`)).json();
      if (scriptResp && scriptResp.script) {
        setEditableScript(scriptResp.script);
        setAppState('script-editing');
      } else {
        setAppState('processing');
      }
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
    setVoiceSpeed(1.5);
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
            selectedSpeed={voiceSpeed}
            onSelect={handleVoiceActorSelect}
            onSpeedChange={handleVoiceSpeedChange}
            onNext={handleStartProcessing}
            isLoading={isLoading}
          />
        );

      case 'script-editing':
        return editableScript ? (
          <ScriptEditor
            projectId={projectId}
            script={editableScript}
            onSave={async (script) => {
              // 保存API
              await fetch(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080'}/api/script/${projectId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(script),
              });
              setEditableScript(script);
            }}
            onNext={async () => {
              setIsLoading(true);
              setError('');
              try {
                // 段階4: 音声設定作成（voice_prompt.yaml 生成）
                await stageAPI.createVoiceSettings(projectId, selectedVoiceActorId, voiceSpeed);
                // 生成待機
                await (async () => {
                  const start = Date.now();
                  const timeoutMs = 120000;
                  while (true) {
                    const status = await projectAPI.getStatus(projectId);
                    if ((status.files || []).includes('voice_prompt.yaml')) break;
                    if (Date.now() - start > timeoutMs) throw new Error('タイムアウト: voice_prompt.yaml');
                    await new Promise(r => setTimeout(r, 1500));
                  }
                })();

                // 段階5: 音声生成（音声/字幕）
                await stageAPI.generateVoice(projectId);
                // 完了待機（audio_combined.wav か subtitle.srt のいずれか）
                await (async () => {
                  const start = Date.now();
                  const timeoutMs = 180000;
                  while (true) {
                    const status = await projectAPI.getStatus(projectId);
                    const files = status.files || [];
                    if (files.includes('audio_combined.wav') || files.includes('subtitle.srt')) break;
                    if (Date.now() - start > timeoutMs) throw new Error('タイムアウト: 音声/字幕生成');
                    await new Promise(r => setTimeout(r, 2000));
                  }
                })();

                // 結果画面へ
                const projectData = await projectAPI.get(projectId);
                setProject(projectData.project);
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
              } catch (e: any) {
                setError(e.message || '次工程の実行に失敗しました');
                setAppState('processing');
              } finally {
                setIsLoading(false);
              }
            }}
            onBack={() => setAppState('voice-actor-selection')}
            isLoading={isLoading}
          />
        ) : (
          <div>台本を読み込み中...</div>
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
