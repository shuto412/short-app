import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  Divider,
  Stack,
  TextField,
} from '@mui/material';
import Button from '@mui/material/Button';
import Autocomplete from '@mui/material/Autocomplete';
import { generationAPI } from '../services/api';
import type { TemplateDetail } from '../types';

interface ScenarioSelectorProps {
  selectedScenario?: string;
  onSelect: (scenarioType: string) => void;
  isLoading?: boolean;
  onNext?: () => void;
}

type Option = { id: string; label: string; category: string };

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  selectedScenario,
  onSelect,
  isLoading = false,
  onNext,
}) => {
  const [templates, setTemplates] = useState<Record<string, TemplateDetail>>({});
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedId, setSelectedId] = useState<string | undefined>(selectedScenario);

  useEffect(() => {
    setSelectedId(selectedScenario);
  }, [selectedScenario]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setLoading(true);
        const data = await generationAPI.getTemplates();
        if (mounted) setTemplates(data);
      } catch (e) {
        console.error('Failed to load templates', e);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const options: Option[] = useMemo(() => {
    return Object.entries(templates).map(([id, t]) => ({
      id,
      label: `${t.category} / ${t.name}`,
      category: t.category,
    }));
  }, [templates]);

  const selectedTemplate = selectedId ? templates[selectedId] : undefined;

  const handleChange = (_: React.SyntheticEvent, value: Option | null) => {
    const newId = value?.id;
    setSelectedId(newId);
    if (newId) onSelect(newId);
  };

  if (isLoading || loading) {
    return (
      <Box sx={{ maxWidth: 900, mx: 'auto', p: 3, textAlign: 'center' }}>
        <Typography variant="h6">シナリオを読み込み中...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', p: 3 }}>
      <Paper elevation={2} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom textAlign="center">
          動画のシナリオを選択
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" textAlign="center" mb={3}>
          コンテンツに最適なシナリオテンプレートを選択してください
        </Typography>

        <Stack direction="column" spacing={3}>
          {/* 上部: タプル選択（カテゴリ / テンプレート名） */}
          <Autocomplete<Option, false, false, false>
            options={options}
            value={options.find((o) => o.id === selectedId) ?? null}
            onChange={handleChange}
            getOptionLabel={(o) => o.label}
            renderInput={(params) => (
              <TextField {...params} label="シナリオ（カテゴリ / テンプレート）" placeholder="例: 教育 / チュートリアル" />
            )}
            fullWidth
          />

          <Divider />

          {/* 下部: 詳細プレビュー */}
          <Card variant="outlined">
            <CardContent>
              {selectedTemplate ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {selectedTemplate.name}
                  </Typography>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    カテゴリ: {selectedTemplate.category}
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedTemplate.description}
                  </Typography>

                  {selectedTemplate.tags && selectedTemplate.tags.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>タグ</Typography>
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {selectedTemplate.tags.map((tag) => (
                          <Chip key={tag} label={`#${tag}`} size="small" />
                        ))}
                      </Stack>
                    </Box>
                  )}

                  <Box>
                    <Typography variant="subtitle2" gutterBottom>構造</Typography>
                    <Stack spacing={0.5}>
                      {(selectedTemplate.structure ?? []).map((s, idx) => {
                        const text = typeof s === 'string'
                          ? s
                          : `${s.type}${s.description ? ` - ${s.description}` : ''}`;
                        return (
                          <Typography key={idx} variant="body2">
                            {idx + 1}. {text}
                          </Typography>
                        );
                      })}
                      {(!selectedTemplate.structure || selectedTemplate.structure.length === 0) && (
                        <Typography variant="body2" color="text.secondary">
                          構造情報はありません
                        </Typography>
                      )}
                    </Stack>
                  </Box>
                </Box>
              ) : (
                <Typography color="text.secondary">テンプレートを選択してください</Typography>
              )}
            </CardContent>
          </Card>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="primary"
              disabled={!selectedId}
              onClick={() => {
                if (selectedId && onNext) onNext();
              }}
            >
              次へ
            </Button>
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
};