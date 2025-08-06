import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  LinearProgress,
  Slider,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  RestoreFromTrash as RestoreIcon,
} from '@mui/icons-material';
import {
  Script,
  Scene,
  ScriptEditorProps,
  VoiceSettings,
  SceneUpdate,
} from '../types';

export const ScriptEditor: React.FC<ScriptEditorProps> = ({
  projectId,
  script: initialScript,
  onSave,
  onNext,
  onBack,
  isLoading = false,
}) => {
  const [script, setScript] = useState<Script>(initialScript);
  const [editingSceneId, setEditingSceneId] = useState<number | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);
  const [hasChanges, setHasChanges] = useState(false);

  // スクリプトが変更されたかを監視
  useEffect(() => {
    const isChanged = JSON.stringify(script) !== JSON.stringify(initialScript);
    setHasChanges(isChanged);
  }, [script, initialScript]);

  // バリデーション
  const validateScript = (scriptToValidate: Script) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!scriptToValidate.scenes || scriptToValidate.scenes.length === 0) {
      errors.push('シーンが1つも設定されていません');
    }

    let totalDuration = 0;
    const sceneIds = new Set<number>();

    scriptToValidate.scenes.forEach((scene, index) => {
      const sceneNum = index + 1;

      // ID重複チェック
      if (sceneIds.has(scene.scene_id)) {
        errors.push(`シーン${sceneNum}: IDが重複しています`);
      }
      sceneIds.add(scene.scene_id);

      // テキストチェック
      if (!scene.text || scene.text.trim().length === 0) {
        errors.push(`シーン${sceneNum}: テキストが空です`);
      } else if (scene.text.length > 500) {
        warnings.push(`シーン${sceneNum}: テキストが長すぎます (${scene.text.length}文字)`);
      } else if (scene.text.length < 10) {
        warnings.push(`シーン${sceneNum}: テキストが短すぎます (${scene.text.length}文字)`);
      }

      // 継続時間チェック
      if (scene.duration <= 0) {
        errors.push(`シーン${sceneNum}: 継続時間が無効です`);
      } else if (scene.duration > 30) {
        warnings.push(`シーン${sceneNum}: 継続時間が長すぎます (${scene.duration}秒)`);
      }

      totalDuration += scene.duration;
    });

    // 全体時間チェック
    if (totalDuration > 300) {
      warnings.push(`全体時間が長すぎます (${totalDuration}秒)`);
    } else if (totalDuration < 10) {
      warnings.push(`全体時間が短すぎます (${totalDuration}秒)`);
    }

    setValidationErrors(errors);
    setValidationWarnings(warnings);

    return errors.length === 0;
  };

  // シーン更新
  const updateScene = (sceneId: number, updates: Partial<Scene>) => {
    const newScript = {
      ...script,
      scenes: script.scenes.map(scene =>
        scene.scene_id === sceneId ? { ...scene, ...updates } : scene
      ),
    };

    // 全体時間を再計算
    const totalDuration = newScript.scenes.reduce((sum, scene) => sum + scene.duration, 0);
    newScript.metadata.total_duration = totalDuration;

    setScript(newScript);
    validateScript(newScript);
  };

  // シーン追加
  const addScene = (position?: number) => {
    const maxId = Math.max(...script.scenes.map(s => s.scene_id), 0);
    const newScene: Scene = {
      scene_id: maxId + 1,
      scene_type: 'main_content',
      duration: 5.0,
      text: '',
      order: position !== undefined ? position : script.scenes.length,
      voice_settings: {
        voice_actor_id: '',
        emotion: 'neutral',
        speed: 1.0,
        pitch: 0,
        volume: 1.0,
        pauseLength: 0.8,
        intonation: 1.0,
      },
    };

    const newScenes = [...script.scenes];
    if (position !== undefined) {
      newScenes.splice(position, 0, newScene);
    } else {
      newScenes.push(newScene);
    }

    const newScript = {
      ...script,
      scenes: newScenes,
    };

    const totalDuration = newScript.scenes.reduce((sum, scene) => sum + scene.duration, 0);
    newScript.metadata.total_duration = totalDuration;

    setScript(newScript);
    setEditingSceneId(newScene.scene_id);
    setShowAddDialog(false);
  };

  // シーン削除
  const deleteScene = (sceneId: number) => {
    if (script.scenes.length <= 1) {
      window.alert('最低1つのシーンが必要です');
      return;
    }

    const newScript = {
      ...script,
      scenes: script.scenes.filter(scene => scene.scene_id !== sceneId),
    };

    const totalDuration = newScript.scenes.reduce((sum, scene) => sum + scene.duration, 0);
    newScript.metadata.total_duration = totalDuration;

    setScript(newScript);
    setEditingSceneId(null);
    validateScript(newScript);
  };

  // 保存
  const handleSave = async () => {
    if (!validateScript(script)) {
      window.alert('エラーがあるため保存できません');
      return;
    }

    try {
      const updatedScript = {
        ...script,
        metadata: {
          ...script.metadata,
          edited: true,
          version: (script.metadata.version || 0) + 1,
        },
      };

      await onSave(updatedScript);
      setHasChanges(false);
    } catch (error) {
      console.error('Save failed:', error);
      window.alert('保存に失敗しました');
    }
  };

  // シーンタイプの選択肢
  const sceneTypes = [
    { value: 'opening', label: 'オープニング' },
    { value: 'main_content', label: 'メインコンテンツ' },
    { value: 'explanation', label: '説明' },
    { value: 'demonstration', label: 'デモンストレーション' },
    { value: 'conclusion', label: '結論' },
    { value: 'cta', label: '行動喚起' },
  ];

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* ヘッダー */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          シナリオ編集
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          動画の台本を確認・編集してください。シーンの順序変更、テキスト編集、音声設定の調整が可能です。
        </Typography>

        {/* メタデータ表示 */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              総シーン数
            </Typography>
            <Typography variant="h6">{script.scenes.length}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              予想時間
            </Typography>
            <Typography variant="h6">{Math.round(script.metadata.total_duration)}秒</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              シナリオタイプ
            </Typography>
            <Typography variant="h6">{script.metadata.scenario_type}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              編集バージョン
            </Typography>
            <Typography variant="h6">v{script.metadata.version}</Typography>
          </Grid>
        </Grid>
      </Box>

      {/* バリデーションメッセージ */}
      {validationErrors.length > 0 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">エラー:</Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </Alert>
      )}

      {validationWarnings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">警告:</Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {validationWarnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      {/* 進捗表示 */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">
            時間配分
          </Typography>
          <Typography variant="body2">
            {Math.round(script.metadata.total_duration)}秒
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={Math.min((script.metadata.total_duration / 60) * 100, 100)}
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>

      {/* シーンリスト */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">シーン一覧</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowAddDialog(true)}
          >
            シーン追加
          </Button>
        </Box>

        {script.scenes.map((scene, index) => (
          <SceneEditor
            key={scene.scene_id}
            scene={scene}
            sceneIndex={index + 1}
            isEditing={editingSceneId === scene.scene_id}
            sceneTypes={sceneTypes}
            onUpdate={(updates) => updateScene(scene.scene_id, updates)}
            onDelete={() => deleteScene(scene.scene_id)}
            onEditToggle={() => 
              setEditingSceneId(editingSceneId === scene.scene_id ? null : scene.scene_id)
            }
          />
        ))}
      </Box>

      {/* アクションボタン */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={onBack}
          disabled={isLoading}
        >
          戻る
        </Button>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={isLoading || !hasChanges || validationErrors.length > 0}
          >
            {hasChanges ? '保存' : '保存済み'}
          </Button>

          <Button
            variant="contained"
            endIcon={<ArrowForwardIcon />}
            onClick={onNext}
            disabled={isLoading || hasChanges || validationErrors.length > 0}
          >
            音声設定へ
          </Button>
        </Box>
      </Box>

      {/* シーン追加ダイアログ */}
      <Dialog open={showAddDialog} onClose={() => setShowAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>新しいシーンを追加</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            新しいシーンを末尾に追加します。追加後、詳細を編集できます。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddDialog(false)}>キャンセル</Button>
          <Button onClick={() => addScene()} variant="contained">追加</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// シーン編集コンポーネント
interface SceneEditorProps {
  scene: Scene;
  sceneIndex: number;
  isEditing: boolean;
  sceneTypes: { value: string; label: string }[];
  onUpdate: (updates: Partial<Scene>) => void;
  onDelete: () => void;
  onEditToggle: () => void;
}

const SceneEditor: React.FC<SceneEditorProps> = ({
  scene,
  sceneIndex,
  isEditing,
  sceneTypes,
  onUpdate,
  onDelete,
  onEditToggle,
}) => {
  const [localScene, setLocalScene] = useState<Scene>(scene);

  // シーンが変更されたら同期
  useEffect(() => {
    setLocalScene(scene);
  }, [scene]);

  const handleFieldChange = (field: keyof Scene, value: any) => {
    const updated = { ...localScene, [field]: value };
    setLocalScene(updated);
    onUpdate(updated);
  };

  const handleVoiceSettingChange = (field: keyof VoiceSettings, value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    onUpdate({
      voice_settings: {
        ...localScene.voice_settings,
        [field]: numValue,
      },
    });
  };

  return (
    <Accordion expanded={isEditing} onChange={onEditToggle}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" sx={{ mr: 2 }}>
            シーン {sceneIndex}
          </Typography>
          <Chip 
            label={sceneTypes.find(t => t.value === scene.scene_type)?.label || scene.scene_type}
            size="small"
            sx={{ mr: 2 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
            {scene.duration}秒
          </Typography>
          <Typography 
            variant="body2" 
            sx={{ 
              flexGrow: 1, 
              overflow: 'hidden', 
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            {scene.text}
          </Typography>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            sx={{ ml: 1 }}
          >
            <DeleteIcon />
          </IconButton>
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        <Grid container spacing={3}>
          {/* 基本設定 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="h6" gutterBottom>基本設定</Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>シーンタイプ</InputLabel>
              <Select
                value={localScene.scene_type}
                onChange={(e) => handleFieldChange('scene_type', e.target.value)}
              >
                {sceneTypes.map(type => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="継続時間（秒）"
              type="number"
              value={localScene.duration}
              onChange={(e) => handleFieldChange('duration', parseFloat(e.target.value) || 0)}
              inputProps={{ min: 0.1, max: 60, step: 0.1 }}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="テキスト"
              multiline
              rows={4}
              value={localScene.text}
              onChange={(e) => handleFieldChange('text', e.target.value)}
              placeholder="このシーンで話すセリフを入力してください..."
            />
          </Grid>

          {/* 音声設定 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="h6" gutterBottom>音声設定</Typography>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>感情</InputLabel>
              <Select
                value={localScene.voice_settings.emotion}
                onChange={(e) => handleVoiceSettingChange('emotion', e.target.value)}
              >
                <MenuItem value="neutral">標準</MenuItem>
                <MenuItem value="cheerful">明るい</MenuItem>
                <MenuItem value="confident">自信のある</MenuItem>
                <MenuItem value="calm">落ち着いた</MenuItem>
                <MenuItem value="excited">興奮した</MenuItem>
              </Select>
            </FormControl>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>話す速度</Typography>
              <Slider
                value={localScene.voice_settings.speed}
                onChange={(_, value) => handleVoiceSettingChange('speed', value)}
                min={0.5}
                max={2.0}
                step={0.1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>ピッチ</Typography>
              <Slider
                value={localScene.voice_settings.pitch}
                onChange={(_, value) => handleVoiceSettingChange('pitch', value)}
                min={-12}
                max={12}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>音量</Typography>
              <Slider
                value={localScene.voice_settings.volume}
                onChange={(_, value) => handleVoiceSettingChange('volume', value)}
                min={0.1}
                max={2.0}
                step={0.1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
};