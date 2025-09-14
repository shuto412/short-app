import React, { useRef, useState } from 'react';
import { Box, Button, Typography } from '@mui/material';
import { markdownAPI } from '../services/api';
import type { MarkdownData } from '../types';

interface MarkdownUploaderProps {
  onUpload: (markdownData: MarkdownData) => void;
  onBack: () => void;
  isLoading?: boolean;
  error?: string;
}

export const MarkdownUploader: React.FC<MarkdownUploaderProps> = ({ onUpload, onBack, isLoading, error }) => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [localError, setLocalError] = useState<string>('');

  const handleFile = async (file: File) => {
    setLocalError('');
    if (!file.name.match(/\.(md|markdown)$/i)) {
      setLocalError('対応形式は .md/.markdown のみです');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setLocalError('ファイルサイズは最大10MBまでです');
      return;
    }
    const text = await file.text();
    const valid = await markdownAPI.validate(text, file.name);
    if (!valid?.valid) {
      setLocalError('Markdownのバリデーションに失敗しました');
      return;
    }
    onUpload({ filename: file.name, content: text, size: file.size, lastModified: file.lastModified });
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Markdownファイルを選択</Typography>
      <input
        ref={inputRef}
        type="file"
        accept=".md,.markdown"
        style={{ display: 'none' }}
        onChange={async (e) => {
          const file = e.target.files?.[0];
          if (file) await handleFile(file);
        }}
      />
      <Button variant="contained" onClick={() => inputRef.current?.click()} disabled={!!isLoading}>
        ファイルを選択
      </Button>
      <Button sx={{ ml: 2 }} onClick={onBack}>戻る</Button>
      {(error || localError) && (
        <Typography color="error" sx={{ mt: 2 }}>{error || localError}</Typography>
      )}
    </Box>
  );
};


