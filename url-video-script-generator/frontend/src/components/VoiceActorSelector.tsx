import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  Button,
  Slider
} from '@mui/material';
import {
  RecordVoiceOver as VoiceIcon,
  Star as StarIcon,
  PlayArrow as PlayIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';
import type { VoiceActorSelectorProps } from '../types';

const DEFAULT_VOICE_ACTOR_ID = '231e0170-0ece-4155-be44-231423062f41';

export const VoiceActorSelector: React.FC<VoiceActorSelectorProps> = ({
  voiceActors,
  selectedVoiceActorId = DEFAULT_VOICE_ACTOR_ID,
  selectedSpeed = 1.5,
  onSelect,
  onSpeedChange,
  onNext,
  isLoading = false
}) => {

  const handleChange = (event: any) => {
    onSelect(event.target.value);
  };

  const handleSpeedChange = (event: Event, newValue: number | number[]) => {
    const speed = Array.isArray(newValue) ? newValue[0] : newValue;
    onSpeedChange?.(speed);
  };

  const speedMarks = [
    { value: 0.5, label: '0.5x' },
    { value: 0.75, label: '0.75x' },
    { value: 1.0, label: '1.0x' },
    { value: 1.25, label: '1.25x' },
    { value: 1.5, label: '1.5x' },
    { value: 2.0, label: '2.0x' }
  ];

  if (isLoading) {
    return (
      <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress size={24} sx={{ mr: 2 }} />
        <Typography variant="body2" color="text.secondary">
          ボイスアクター一覧を読み込み中...
        </Typography>
      </Paper>
    );
  }

  if (!voiceActors || voiceActors.length === 0) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        ボイスアクターが見つかりませんでした。デフォルトのボイスアクターを使用します。
      </Alert>
    );
  }

  // デフォルトボイスアクターを見つける
  const defaultActor = voiceActors.find(actor => actor.id === DEFAULT_VOICE_ACTOR_ID);

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <VoiceIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6">
          ボイスアクター選択
        </Typography>
      </Box>

      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel id="voice-actor-select-label">ボイスアクター</InputLabel>
        <Select
          labelId="voice-actor-select-label"
          value={selectedVoiceActorId}
          label="ボイスアクター"
          onChange={handleChange}
          disabled={isLoading}
        >
          {voiceActors.map((actor) => (
            <MenuItem key={actor.id} value={actor.id}>
              <Box display="flex" alignItems="center" width="100%">
                <Box flexGrow={1}>
                  <Typography variant="body1" component="span">
                    {actor.name}
                  </Typography>
                  {actor.description && (
                    <Typography variant="body2" color="text.secondary" component="div">
                      {actor.description}
                    </Typography>
                  )}
                </Box>
                {actor.id === DEFAULT_VOICE_ACTOR_ID && (
                  <Chip
                    icon={<StarIcon />}
                    label="推奨"
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{ ml: 1 }}
                  />
                )}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      {/* 音声速度設定 */}
      <Box sx={{ mt: 3, mb: 2 }}>
        <Box display="flex" alignItems="center" mb={2}>
          <SpeedIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">
            音声速度設定
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            現在の速度: {selectedSpeed}x
          </Typography>
          <Slider
            value={selectedSpeed}
            onChange={handleSpeedChange}
            min={0.5}
            max={2.0}
            step={0.25}
            marks={speedMarks}
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => `${value}x`}
            disabled={isLoading}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            0.5x（ゆっくり）～ 2.0x（速い）まで調整可能です
          </Typography>
        </Box>
      </Box>

      {defaultActor && selectedVoiceActorId === DEFAULT_VOICE_ACTOR_ID && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>推奨ボイスアクター:</strong> {defaultActor.name}
            {defaultActor.description && ` - ${defaultActor.description}`}
          </Typography>
        </Alert>
      )}

      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        選択されたボイスアクターで全ての音声が生成されます。
        生成後にボイスアクターを変更したい場合は、新しいプロジェクトを作成してください。
      </Typography>

      {onNext && (
        <Button
          variant="contained"
          color="primary"
          size="large"
          fullWidth
          onClick={onNext}
          disabled={isLoading || !selectedVoiceActorId}
          startIcon={isLoading ? <CircularProgress size={20} /> : <PlayIcon />}
          sx={{ mt: 3 }}
        >
          {isLoading ? '処理開始中...' : '動画台本生成を開始'}
        </Button>
      )}
    </Paper>
  );
};