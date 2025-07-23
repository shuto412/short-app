import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  InputAdornment,
  CircularProgress
} from '@mui/material';
import {
  Language as LanguageIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { isValidUrl, normalizeUrl } from '../utils/helpers';
import type { UrlInputProps } from '../types';

export const UrlInput: React.FC<UrlInputProps> = ({ 
  onSubmit, 
  isLoading = false, 
  error 
}) => {
  const [url, setUrl] = useState('');
  const [localError, setLocalError] = useState('');

  const validateUrl = (inputUrl: string): string | null => {
    if (!inputUrl.trim()) {
      return 'URLを入力してください';
    }

    const normalizedUrl = normalizeUrl(inputUrl.trim());
    
    if (!isValidUrl(normalizedUrl)) {
      return '有効なURLを入力してください';
    }

    // 危険なプロトコルをチェック
    if (normalizedUrl.startsWith('file://') || normalizedUrl.startsWith('javascript:')) {
      return 'このプロトコルはサポートされていません';
    }

    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateUrl(url);
    if (validationError) {
      setLocalError(validationError);
      return;
    }

    setLocalError('');
    const normalizedUrl = normalizeUrl(url.trim());
    onSubmit(normalizedUrl);
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value;
    setUrl(newUrl);
    
    // リアルタイムバリデーション
    if (localError && newUrl.trim()) {
      const validationError = validateUrl(newUrl);
      if (!validationError) {
        setLocalError('');
      }
    }
  };

  const exampleUrls = [
    'https://example.com/product',
    'https://github.com/repository',
    'https://blog.example.com/article',
    'https://docs.example.com/guide'
  ];

  const handleExampleClick = (exampleUrl: string) => {
    setUrl(exampleUrl);
    setLocalError('');
  };

  const displayError = localError || error;

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box textAlign="center" mb={4}>
          <LanguageIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            URL動画台本生成システム
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            URLから自動的にコンテンツを取得し、AI（Claude）を活用して動画台本を生成します
          </Typography>
        </Box>

        {displayError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {displayError}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="ウェブページのURL"
            value={url}
            onChange={handleUrlChange}
            error={!!displayError}
            placeholder="https://example.com"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LanguageIcon color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 3 }}
            disabled={isLoading}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={!url.trim() || isLoading || !!displayError}
            startIcon={isLoading ? <CircularProgress size={20} /> : <SendIcon />}
            sx={{ mb: 3 }}
          >
            {isLoading ? '処理中...' : '動画台本を生成'}
          </Button>
        </Box>

        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            サンプルURL:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {exampleUrls.map((exampleUrl, index) => (
              <Button
                key={index}
                size="small"
                variant="outlined"
                onClick={() => handleExampleClick(exampleUrl)}
                disabled={isLoading}
                sx={{ fontSize: '0.75rem' }}
              >
                {exampleUrl}
              </Button>
            ))}
          </Box>
        </Box>

        <Box mt={4}>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            対応形式: ウェブページ、ブログ記事、製品ページ、ドキュメントなど
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
}; 