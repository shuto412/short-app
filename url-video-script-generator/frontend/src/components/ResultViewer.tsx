import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Paper, 
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Divider
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  VolumeUp as VolumeIcon
} from '@mui/icons-material';
import { generationAPI } from '../services/api';
import type { AudioFilesResponse, AudioSegment, Project, GeneratedFile } from '../types';

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
  const [audioFiles, setAudioFiles] = useState<AudioFilesResponse | null>(null);
  const [showAudioSegments, setShowAudioSegments] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);

  useEffect(() => {
    const loadAudioFiles = async () => {
      try {
        const audioData = await generationAPI.getAudioFiles(projectId);
        setAudioFiles(audioData);
      } catch (error) {
        console.error('Failed to load audio files:', error);
      }
    };

    if (projectId) {
      loadAudioFiles();
    }
  }, [projectId]);

  const handleDownload = (file: GeneratedFile) => {
    const link = document.createElement('a');
    link.href = file.downloadUrl;
    link.download = file.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleAudioSegmentDownload = (segment: AudioSegment) => {
    const link = document.createElement('a');
    link.href = generationAPI.downloadAudioSegment(projectId, segment.filename);
    link.download = segment.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePlayAudio = (url: string) => {
    // 現在再生中の音声を停止
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }

    // 新しい音声を再生
    const audio = new Audio(url);
    audio.play();
    setCurrentAudio(audio);

    // 再生終了時のクリーンアップ
    audio.addEventListener('ended', () => {
      setCurrentAudio(null);
    });
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

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
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

      {/* 音声ファイル個別表示 */}
      {audioFiles && audioFiles.audio_files.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h5">
              音声ファイル ({audioFiles.total_files}個のセグメント)
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setShowAudioSegments(!showAudioSegments)}
              endIcon={showAudioSegments ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            >
              {showAudioSegments ? '非表示' : '個別表示'}
            </Button>
          </Box>

          {/* 統合音声ファイル */}
          <Card variant="outlined" sx={{ mb: 2, bgcolor: 'primary.50' }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box display="flex" alignItems="center" gap={2}>
                  <VolumeIcon color="primary" />
                  <Box>
                    <Typography variant="h6" color="primary">
                      統合音声ファイル
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      全セグメントを結合した音声ファイル
                    </Typography>
                  </Box>
                </Box>
                <Box display="flex" gap={1}>
                  <IconButton
                    color="primary"
                    onClick={() => handlePlayAudio(audioFiles.combined_audio_url)}
                    title="再生"
                  >
                    <PlayIcon />
                  </IconButton>
                  <IconButton
                    color="primary"
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = audioFiles.combined_audio_url;
                      link.download = 'audio_combined.wav';
                      link.click();
                    }}
                    title="ダウンロード"
                  >
                    <DownloadIcon />
                  </IconButton>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* 個別音声セグメント */}
          <Collapse in={showAudioSegments}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              個別音声セグメント
            </Typography>
            <List>
              {audioFiles.audio_files.map((segment, index) => (
                <React.Fragment key={segment.segment_id}>
                  <ListItem
                    sx={{
                      bgcolor: segment.exists ? 'background.paper' : 'grey.100',
                      borderRadius: 1,
                      mb: 1,
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <ListItemIcon>
                      <Chip 
                        label={`#${index + 1}`} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="subtitle2">
                            {segment.filename}
                          </Typography>
                          {segment.error && (
                            <Chip label="エラー" size="small" color="error" />
                          )}
                          {!segment.exists && (
                            <Chip label="ファイルなし" size="small" color="warning" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {segment.text.substring(0, 100)}
                            {segment.text.length > 100 ? '...' : ''}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            サイズ: {(segment.size_bytes / 1024).toFixed(1)}KB
                            {segment.duration > 0 && ` | 長さ: ${segment.duration.toFixed(1)}秒`}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1}>
                        {segment.exists && (
                          <>
                            <IconButton
                              size="small"
                              onClick={() => handlePlayAudio(segment.download_url)}
                              title="再生"
                              disabled={!segment.exists}
                            >
                              <PlayIcon />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleAudioSegmentDownload(segment)}
                              title="ダウンロード"
                              disabled={!segment.exists}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </>
                        )}
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < audioFiles.audio_files.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Collapse>
        </Paper>
      )}
    </Box>
  );
}; 