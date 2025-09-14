import React from 'react';
import { Box, Button, Chip, Divider, Typography } from '@mui/material';
import { markdownAPI, projectAPI } from '../services/api';
import type { MarkdownData } from '../types';

interface MarkdownPreviewProps {
  markdown: MarkdownData;
  onNext: (projectId: string) => void;
  onBack: () => void;
  scenarioType: string;
}

export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ markdown, onNext, onBack, scenarioType }) => {
  const [meta, setMeta] = React.useState<any>(null);
  const [preview, setPreview] = React.useState<string>('');
  const [quality, setQuality] = React.useState<number>(0);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string>('');

  React.useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setError('');
        const resp = await markdownAPI.preview(markdown.content, markdown.filename);
        setMeta({ title: resp.title, description: resp.description, category: resp.category, tags: resp.tags });
        setPreview(resp.preview);
        setQuality(resp.quality);
      } catch (e: any) {
        setError(e?.message || 'プレビューの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [markdown]);

  const handleCreate = async () => {
    try {
      setLoading(true);
      setError('');
      const result = await projectAPI.create({
        input_source: 'markdown',
        markdown_content: markdown.content,
        markdown_filename: markdown.filename,
        scenario_type: scenarioType || 'product_introduction',
        options: {},
      });
      onNext(result.project_id);
    } catch (e: any) {
      setError(e?.message || 'プロジェクト作成に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6">プレビュー</Typography>
      {meta?.title && <Typography sx={{ mt: 1 }}><b>タイトル:</b> {meta.title}</Typography>}
      {meta?.description && <Typography sx={{ mt: 1 }}><b>説明:</b> {meta.description}</Typography>}
      <Box sx={{ my: 1 }}>
        {meta?.tags?.map((t: string) => (
          <Chip key={t} label={t} size="small" sx={{ mr: 1 }} />
        ))}
      </Box>
      <Typography variant="body2" color="text.secondary">品質スコア: {quality.toFixed(1)}</Typography>
      <Divider sx={{ my: 2 }} />
      <Typography variant="subtitle2" gutterBottom>冒頭500文字</Typography>
      <Box sx={{ p: 2, bgcolor: '#fafafa', borderRadius: 1, whiteSpace: 'pre-wrap' }}>
        {preview}
      </Box>
      {error && <Typography color="error" sx={{ mt: 2 }}>{error}</Typography>}
      <Box sx={{ mt: 2 }}>
        <Button onClick={onBack} sx={{ mr: 2 }}>戻る</Button>
        <Button variant="contained" onClick={handleCreate} disabled={loading}>この内容でプロジェクト作成</Button>
      </Box>
    </Box>
  );
};


