import React from 'react';
import { Box, Card, CardActionArea, CardContent, Typography } from '@mui/material';

export type InputSource = 'url' | 'markdown';

interface InformationSourceSelectorProps {
  onSelect: (source: InputSource) => void;
  isLoading?: boolean;
}

export const InformationSourceSelector: React.FC<InformationSourceSelectorProps> = ({ onSelect }) => {
  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 2 }}>情報源を選択してください</Typography>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
          gap: 3,
        }}
      >
        <Card>
          <CardActionArea onClick={() => onSelect('url')}>
            <CardContent>
              <Typography variant="h6">サイトから</Typography>
              <Typography variant="body2" color="text.secondary">
                URLを入力してスクレイピングし、要約から台本を生成します。
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>
        <Card>
          <CardActionArea onClick={() => onSelect('markdown')}>
            <CardContent>
              <Typography variant="h6">.mdファイルから</Typography>
              <Typography variant="body2" color="text.secondary">
                Markdownファイルをアップロードし、内容から台本を生成します。
              </Typography>
            </CardContent>
          </CardActionArea>
        </Card>
      </Box>
    </Box>
  );
};
