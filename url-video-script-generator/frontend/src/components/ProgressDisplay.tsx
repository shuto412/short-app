import React from 'react';
import { Box, Typography, LinearProgress, List, ListItem, ListItemText, Paper } from '@mui/material';

interface ProcessingStatus {
  project_id: string;
  status: string;
  progress: {
    percentage: number;
    completed_steps: number;
    total_steps: number;
    steps: Array<{
      step: string;
      completed: boolean;
      file: string;
    }>;
  };
  files: string[];
  last_updated: string;
}

interface ProgressDisplayProps {
  status: ProcessingStatus;
  isVisible: boolean;
}

export const ProgressDisplay: React.FC<ProgressDisplayProps> = ({ status, isVisible }) => {
  if (!isVisible) {
    return null;
  }

  const isProcessing = status.status === 'processing';
  const isCompleted = status.status === 'completed';
  const isFailed = status.status === 'failed';

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom textAlign="center">
          {isCompleted ? '処理完了！' : isFailed ? '処理失敗' : '動画台本を生成中...'}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" textAlign="center" mb={4}>
          {isCompleted 
            ? 'すべてのファイルが正常に生成されました'
            : isFailed 
            ? 'エラーが発生しました'
            : 'しばらくお待ちください'
          }
        </Typography>

        <Box mb={4}>
          <Typography variant="h6" mb={1}>
            全体の進捗 ({status.progress.completed_steps}/{status.progress.total_steps})
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={status.progress.percentage} 
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {Math.round(status.progress.percentage)}% 完了
          </Typography>
        </Box>

        <Typography variant="h6" gutterBottom>
          処理ステップ
        </Typography>
        <List>
          {status.progress.steps.map((step, index) => (
            <ListItem key={index}>
              <ListItemText
                primary={step.step}
                secondary={step.completed ? `完了 - ${step.file}` : '待機中'}
              />
            </ListItem>
          ))}
        </List>

        {status.files.length > 0 && (
          <Box mt={3}>
            <Typography variant="h6" gutterBottom>
              生成済みファイル ({status.files.length}個)
            </Typography>
            <Typography variant="body2">
              {status.files.join(', ')}
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
};
