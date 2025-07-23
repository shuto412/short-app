import React from 'react';
import { Box, Typography, Button, Card, CardContent, Paper } from '@mui/material';

interface Project {
  id: string;
  title: string;
  url: string;
  scenario_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface GeneratedFile {
  name: string;
  type: string;
  downloadUrl: string;
}

interface ResultViewerProps {
  projectId: string;
  project: Project;
  files: GeneratedFile[];
  onStartNew: () => void;
}

export const ResultViewer: React.FC<ResultViewerProps> = ({
  projectId,
  project,
  files,
  onStartNew
}) => {
  const handleDownload = (file: GeneratedFile) => {
    const link = document.createElement('a');
    link.href = file.downloadUrl;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const primaryFiles = files.filter(file => 
    ['script', 'audio', 'subtitle'].includes(file.type)
  );

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom textAlign="center">
          動画台本の生成が完了しました！
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" textAlign="center" mb={4}>
          すべてのファイルが正常に生成されました
        </Typography>

        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              プロジェクト情報
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  タイトル: {project.title}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  シナリオ: {project.scenario_type}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        <Box display="flex" justifyContent="center" gap={2} mb={4}>
          <Button variant="contained" onClick={onStartNew} size="large">
            新しい台本を作成
          </Button>
        </Box>
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          ダウンロード可能ファイル
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 2 }}>
          {files.map((file, index) => (
            <Card key={index} variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h6" gutterBottom>
                  {file.type}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {file.name}
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => handleDownload(file)}
                  sx={{ mt: 2 }}
                >
                  ダウンロード
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}; 