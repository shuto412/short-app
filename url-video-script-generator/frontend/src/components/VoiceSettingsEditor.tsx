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
  Divider,
  Paper,
  List,
  ListItem,
  ListItemText,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  VolumeUp as VolumeIcon,
  Speed as SpeedIcon,
  Tune as TuneIcon,
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  ArrowForward as ArrowForwardIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import {
  VoicePrompt,
  VoiceSegment,
  VoiceSettingsEditorProps,
  VoiceParameters,
} from '../types';
import { stageAPI } from '../services/api';

export const VoiceSettingsEditor: React.FC<VoiceSettingsEditorProps> = ({
  projectId,
  voicePrompt: initialVoicePrompt,
  onSave,
  onGenerate,
  onBack,
  isLoading = false,
}) => {
  const [voicePrompt, setVoicePrompt] = useState<VoicePrompt>(initialVoicePrompt);
  const [editingSegmentId, setEditingSegmentId] = useState<number | null>(null);
  const [showBatchUpdateDialog, setShowBatchUpdateDialog] = useState(false);
  const [batchParameters, setBatchParameters] = useState<Partial<VoiceParameters>>({});
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [previewLoading, setPreviewLoading] = useState<number | null>(null);

  // 音声プロンプトが変更されたかを監視
  useEffect(() => {
    const isChanged = JSON.stringify(voicePrompt) !== JSON.stringify(initialVoicePrompt);
    setHasChanges(isChanged);
  }, [voicePrompt, initialVoicePrompt]);

  // バリデーション
  const validateVoicePrompt = (promptToValidate: VoicePrompt) => {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!promptToValidate.segments || promptToValidate.segments.length === 0) {
      errors.push('音声セグメントが1つも設定されていません');
    }

    let totalDuration = 0;
    const segmentIds = new Set<number>();

    promptToValidate.segments.forEach((segment, index) => {
      const segmentNum = index + 1;

      // ID重複チェック
      if (segmentIds.has(segment.segment_id)) {
        errors.push(`セグメント${segmentNum}: IDが重複しています`);
      }
      segmentIds.add(segment.segment_id);

      // テキストチェック
      if (!segment.text || segment.text.trim().length === 0) {
        errors.push(`セグメント${segmentNum}: テキストが空です`);
      }

      // 時間チェック
      if (segment.end_time <= segment.start_time) {
        errors.push(`セグメント${segmentNum}: 終了時間が開始時間以下です`);
      }

      const duration = segment.end_time - segment.start_time;
      if (duration > 30) {
        warnings.push(`セグメント${segmentNum}: 継続時間が長すぎます (${duration.toFixed(1)}秒)`);
      }

      totalDuration = Math.max(totalDuration, segment.end_time);

      // パラメータチェック
      const params = segment.parameters;
      if (params) {
        const speed = params.speed;
        if (speed < 0.5 || speed > 2.0) {
          warnings.push(`セグメント${segmentNum}: 速度が推奨範囲外です (${speed})`);
        }

        const pitch = params.pitch;
        if (pitch < -12 || pitch > 12) {
          warnings.push(`セグメント${segmentNum}: ピッチが推奨範囲外です (${pitch})`);
        }

        const volume = params.volume;
        if (volume < 0.1 || volume > 2.0) {
          warnings.push(`セグメント${segmentNum}: ボリュームが推奨範囲外です (${volume})`);
        }
      }
    });

    // 全体時間チェック
    if (totalDuration > 300) {
      warnings.push(`全体時間が長すぎます (${totalDuration.toFixed(1)}秒)`);
    }

    setValidationErrors(errors);
    setValidationWarnings(warnings);

    return errors.length === 0;
  };

  // セグメント更新
  const updateSegment = (segmentId: number, updates: Partial<VoiceSegment>) => {
    const newVoicePrompt = {
      ...voicePrompt,
      segments: voicePrompt.segments.map(segment =>
        segment.segment_id === segmentId ? { ...segment, ...updates } : segment
      ),
    };

    setVoicePrompt(newVoicePrompt);
    validateVoicePrompt(newVoicePrompt);
  };

  // パラメータ一括更新
  const handleBatchUpdate = async () => {
    try {
      const response = await stageAPI.batchUpdateVoiceParameters(projectId, batchParameters);
      
      // 更新されたプロンプトをサーバーから取得
      const updatedPrompt = await stageAPI.getVoicePrompt(projectId);
      setVoicePrompt(updatedPrompt);
      
      setShowBatchUpdateDialog(false);
      setBatchParameters({});
      
      window.alert('パラメータを一括更新しました');
    } catch (error) {
      console.error('Batch update failed:', error);
      window.alert('一括更新に失敗しました');
    }
  };

  // プレビュー
  const handlePreview = async (segmentId: number) => {
    setPreviewLoading(segmentId);
    
    try {
      const response = await stageAPI.previewVoiceSegment(projectId, segmentId);
      
      // プレビュー情報を表示
      window.alert(`プレビュー: ${response.preview_description}\n推定時間: ${response.estimated_duration.toFixed(1)}秒`);
    } catch (error) {
      console.error('Preview failed:', error);
      window.alert('プレビューに失敗しました');
    } finally {
      setPreviewLoading(null);
    }
  };

  // オリジナルにリセット
  const handleReset = async () => {
    if (!window.confirm('オリジナル設定にリセットしますか？現在の変更は失われます。')) {
      return;
    }

    try {
      const response = await stageAPI.resetVoicePrompt(projectId);
      setVoicePrompt(response.voice_prompt);
      setHasChanges(false);
      window.alert('オリジナル設定にリセットしました');
    } catch (error) {
      console.error('Reset failed:', error);
      window.alert('リセットに失敗しました');
    }
  };

  // 保存
  const handleSave = async () => {
    if (!validateVoicePrompt(voicePrompt)) {
      window.alert('エラーがあるため保存できません');
      return;
    }

    try {
      await onSave(voicePrompt);
      setHasChanges(false);
    } catch (error) {
      console.error('Save failed:', error);
      window.alert('保存に失敗しました');
    }
  };

  // 総時間計算
  const totalDuration = voicePrompt.segments.reduce((max, segment) => 
    Math.max(max, segment.end_time), 0
  );

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* ヘッダー */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          音声設定編集
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          音声のパラメータを調整してください。各セグメントごとに詳細な設定が可能です。
        </Typography>

        {/* メタデータ表示 */}
        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              セグメント数
            </Typography>
            <Typography variant="h6">{voicePrompt.segments.length}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              総時間
            </Typography>
            <Typography variant="h6">{totalDuration.toFixed(1)}秒</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              ボイスアクター
            </Typography>
            <Typography variant="h6">{voicePrompt.api_settings?.voice_actor_id || '未設定'}</Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Typography variant="body2" color="text.secondary">
              出力形式
            </Typography>
            <Typography variant="h6">{voicePrompt.api_settings?.output_format?.toUpperCase() || 'MP3'}</Typography>
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

      {/* 時間進捗表示 */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">
            全体時間
          </Typography>
          <Typography variant="body2">
            {totalDuration.toFixed(1)}秒
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={Math.min((totalDuration / 60) * 100, 100)}
          sx={{ height: 8, borderRadius: 4 }}
        />
      </Box>

      {/* クイックアクション */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          クイックアクション
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<TuneIcon />}
            onClick={() => setShowBatchUpdateDialog(true)}
          >
            一括設定
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleReset}
          >
            リセット
          </Button>
        </Box>
      </Paper>

      {/* セグメントリスト */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          音声セグメント一覧
        </Typography>

        {voicePrompt.segments.map((segment, index) => (
          <VoiceSegmentEditor
            key={segment.segment_id}
            segment={segment}
            segmentIndex={index + 1}
            isEditing={editingSegmentId === segment.segment_id}
            isPreviewLoading={previewLoading === segment.segment_id}
            onUpdate={(updates) => updateSegment(segment.segment_id, updates)}
            onPreview={() => handlePreview(segment.segment_id)}
            onEditToggle={() => 
              setEditingSegmentId(editingSegmentId === segment.segment_id ? null : segment.segment_id)
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
          シナリオ編集へ戻る
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
            onClick={onGenerate}
            disabled={isLoading || hasChanges || validationErrors.length > 0}
          >
            音声生成開始
          </Button>
        </Box>
      </Box>

      {/* 一括更新ダイアログ */}
      <Dialog 
        open={showBatchUpdateDialog} 
        onClose={() => setShowBatchUpdateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>音声パラメータ一括設定</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            以下の設定をすべてのセグメントに適用します。空欄の項目は変更されません。
          </Typography>
          
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>話す速度</Typography>
                <Slider
                  value={batchParameters.speed || 1.0}
                  onChange={(_, value) => setBatchParameters({...batchParameters, speed: value})}
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
                  value={batchParameters.pitch || 0}
                  onChange={(_, value) => setBatchParameters({...batchParameters, pitch: value})}
                  min={-12}
                  max={12}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </Grid>

            <Grid size={{ xs: 12, sm: 6 }}>
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>音量</Typography>
                <Slider
                  value={batchParameters.volume || 1.0}
                  onChange={(_, value) => setBatchParameters({...batchParameters, volume: value})}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>ポーズの長さ</Typography>
                <Slider
                  value={batchParameters.pauseLength || 0.8}
                  onChange={(_, value) => setBatchParameters({...batchParameters, pauseLength: value})}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBatchUpdateDialog(false)}>キャンセル</Button>
          <Button onClick={handleBatchUpdate} variant="contained">適用</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// 音声セグメント編集コンポーネント
interface VoiceSegmentEditorProps {
  segment: VoiceSegment;
  segmentIndex: number;
  isEditing: boolean;
  isPreviewLoading: boolean;
  onUpdate: (updates: Partial<VoiceSegment>) => void;
  onPreview: () => void;
  onEditToggle: () => void;
}

const VoiceSegmentEditor: React.FC<VoiceSegmentEditorProps> = ({
  segment,
  segmentIndex,
  isEditing,
  isPreviewLoading,
  onUpdate,
  onPreview,
  onEditToggle,
}) => {
  const [localSegment, setLocalSegment] = useState<VoiceSegment>(segment);

  // セグメントが変更されたら同期
  useEffect(() => {
    setLocalSegment(segment);
  }, [segment]);

  const handleParameterChange = (field: keyof VoiceParameters, value: string | number) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    const updatedParameters = { ...localSegment.parameters, [field]: numValue };
    const updated = { ...localSegment, parameters: updatedParameters };
    setLocalSegment(updated);
    onUpdate(updated);
  };

  const duration = segment.end_time - segment.start_time;

  return (
    <Accordion expanded={isEditing} onChange={onEditToggle}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" sx={{ mr: 2 }}>
            セグメント {segmentIndex}
          </Typography>
          <Chip 
            label={`${duration.toFixed(1)}秒`}
            size="small"
            sx={{ mr: 2 }}
          />
          <Typography 
            variant="body2" 
            sx={{ 
              flexGrow: 1, 
              overflow: 'hidden', 
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}
          >
            {segment.text}
          </Typography>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onPreview();
            }}
            disabled={isPreviewLoading}
            sx={{ ml: 1 }}
          >
            {isPreviewLoading ? <StopIcon /> : <PlayIcon />}
          </IconButton>
        </Box>
      </AccordionSummary>

      <AccordionDetails>
        <Grid container spacing={3}>
          {/* テキスト情報 */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="h6" gutterBottom>セグメント情報</Typography>
            
            <Typography variant="body2" color="text.secondary" gutterBottom>
              開始時間: {segment.start_time.toFixed(1)}秒
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              終了時間: {segment.end_time.toFixed(1)}秒
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              継続時間: {duration.toFixed(1)}秒
            </Typography>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="body2" fontWeight="bold" gutterBottom>
              テキスト:
            </Typography>
            <Typography variant="body2">
              {segment.text}
            </Typography>
          </Grid>

          {/* 音声パラメータ */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Typography variant="h6" gutterBottom>音声パラメータ</Typography>
            
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, sm: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography gutterBottom>話す速度</Typography>
                  <Slider
                    value={localSegment.parameters.speed}
                    onChange={(_, value) => handleParameterChange('speed', value)}
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
                    value={localSegment.parameters.pitch}
                    onChange={(_, value) => handleParameterChange('pitch', value)}
                    min={-12}
                    max={12}
                    step={1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>
              </Grid>

              <Grid size={{ xs: 12, sm: 6 }}>
                <Box sx={{ mb: 2 }}>
                  <Typography gutterBottom>音量</Typography>
                  <Slider
                    value={localSegment.parameters.volume}
                    onChange={(_, value) => handleParameterChange('volume', value)}
                    min={0.1}
                    max={2.0}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography gutterBottom>ポーズの長さ</Typography>
                  <Slider
                    value={localSegment.parameters.pauseLength || 0.8}
                    onChange={(_, value) => handleParameterChange('pauseLength', value)}
                    min={0.1}
                    max={2.0}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Box>
              </Grid>
            </Grid>

            <Button
              variant="outlined"
              startIcon={<PlayIcon />}
              onClick={onPreview}
              disabled={isPreviewLoading}
              sx={{ mt: 2 }}
            >
              {isPreviewLoading ? 'プレビュー中...' : 'プレビュー'}
            </Button>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
};