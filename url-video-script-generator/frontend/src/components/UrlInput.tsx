import React, { useState } from 'react';
import { Box, TextField, Button, Typography, Paper } from '@mui/material';

interface UrlInputProps {
  onSubmit: (url: string) => void;
  isLoading?: boolean;
  error?: string;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onSubmit, isLoading, error }) => {
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom textAlign="center">
          URL動画台本生成システム
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" textAlign="center" mb={4}>
          URLから自動的に動画台本を生成します
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="ウェブページのURL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            error={!!error}
            helperText={error}
            placeholder="https://example.com"
            sx={{ mb: 3 }}
            disabled={isLoading}
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={!url.trim() || isLoading}
          >
            {isLoading ? '処理中...' : '動画台本を生成'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};
