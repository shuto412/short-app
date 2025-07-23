import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Card,
  CardContent,
  Chip
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as PendingIcon,
  AutoFixHigh as ProcessingIcon,
  Language as ScrapeIcon,
  Summarize as SummaryIcon,
  Movie as ScriptIcon,
  RecordVoiceOver as VoiceIcon,
  Subtitles as SubtitleIcon
} from '@mui/icons-material';
import type { ProgressDisplayProps, ProcessingStep } from '../types';
import { formatRelativeTime } from '../utils/helpers';

export const ProgressDisplay: React.FC<ProgressDisplayProps> = ({
  status,
  isVisible
}) => {
  if (!isVisible || !status) {
    return null;
  }

  const getStepIcon = (stepName: string) => {
    switch (stepName) {
      case 'スクレイピング':
        return <ScrapeIcon />;
      case '要約生成':
        return <SummaryIcon />;
      case '台本生成':
        return <ScriptIcon />;
      case '音声プロンプト作成':
        return <VoiceIcon />;
      case '音声生成':
        return <VoiceIcon />;
      case '字幕生成':
        return <SubtitleIcon />;
      default:
        return <ProcessingIcon />;
    }
  };

  const getStatusIcon = (completed: boolean, isCurrentStep: boolean) => {
    if (completed) {
      return <CheckIcon color="success" />;
    } else if (isCurrentStep) {
      return <ProcessingIcon color="primary" sx={{ animation: 'spin 2s linear infinite' }} />;
    } else {
      return <PendingIcon color="disabled" />;
    }
  };

  const getStatusColor = (statusValue: string): 'success' | 'error' | 'info' | 'warning' => {
    switch (statusValue) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'processing':
        return 'info';
      default:
        return 'warning';
    }
  };

  const currentStepIndex = status.progress.steps.findIndex((step: ProcessingStep) => !step.completed);
  const isProcessing = status.status === 'processing';
  const isCompleted = status.status === 'completed';
  const isFailed = status.status === 'failed';

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box textAlign="center" mb={4}>
          <ProcessingIcon 
            sx={{ 
              fontSize: 60, 
              color: 'primary.main', 
              mb: 2,
              animation: isProcessing ? 'spin 2s linear infinite' : 'none'
            }} 
          />
          <Typography variant="h4" gutterBottom>
            {isCompleted ? '処理完了！' : isFailed ? '処理失敗' : '動画台本を生成中...'}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {isCompleted 
              ? 'すべてのファイルが正常に生成されました'
              : isFailed 
              ? 'エラーが発生しました。しばらくしてからもう一度お試しください'
              : 'しばらくお待ちください。処理には数分かかる場合があります'
            }
          </Typography>
        </Box>

        {/* 全体の進捗バー */}
        <Box mb={4}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">
              全体の進捗
            </Typography>
            <Chip 
              label={`${status.progress.completed_steps}/${status.progress.total_steps} 完了`}
              color={getStatusColor(status.status)}
              size="small"
            />
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={status.progress.percentage} 
            sx={{ height: 8, borderRadius: 4 }}
            color={getStatusColor(status.status)}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {Math.round(status.progress.percentage)}% 完了
          </Typography>
        </Box>

        {/* ステップ詳細 */}
        <Card variant="outlined" sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              処理ステップ
            </Typography>
            
            <List>
              {status.progress.steps.map((step: ProcessingStep, index: number) => {
                const isCurrentStep = index === currentStepIndex && isProcessing;
                
                return (
                  <ListItem key={index} sx={{ py: 1 }}>
                    <ListItemIcon>
                      {getStatusIcon(step.completed, isCurrentStep)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          {getStepIcon(step.step)}
                          <Typography 
                            variant="body1"
                            sx={{ 
                              fontWeight: isCurrentStep ? 'bold' : 'normal',
                              color: step.completed ? 'success.main' : isCurrentStep ? 'primary.main' : 'text.primary'
                            }}
                          >
                            {step.step}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2" color="text.secondary">
                          {step.completed 
                            ? `完了 - ${step.file}` 
                            : isCurrentStep 
                            ? '処理中...' 
                            : '待機中'
                          }
                        </Typography>
                      }
                    />
                  </ListItem>
                );
              })}
            </List>
          </CardContent>
        </Card>

        {/* 生成されたファイル一覧 */}
        {status.files.length > 0 && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                生成済みファイル ({status.files.length}個)
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {status.files.map((file: string, index: number) => (
                  <Chip 
                    key={index}
                    label={file}
                    variant="outlined"
                    size="small"
                    color="success"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>
        )}

        {/* 最終更新時刻 */}
        <Box mt={3} textAlign="center">
          <Typography variant="body2" color="text.secondary">
            最終更新: {formatRelativeTime(status.last_updated || status.updated_at || new Date().toISOString())}
          </Typography>
        </Box>
      </Paper>

      {/* CSS アニメーション */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </Box>
  );
}; 