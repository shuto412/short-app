import React from 'react';
import { Box, Typography, Card, CardContent, CardActionArea, Paper } from '@mui/material';

interface Scenario {
  id: string;
  name: string;
  description: string;
}

interface ScenarioSelectorProps {
  scenarios: Scenario[];
  selectedScenario: string;
  onSelect: (scenarioType: string) => void;
  isLoading?: boolean;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  scenarios,
  selectedScenario,
  onSelect,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <Box sx={{ maxWidth: 800, mx: 'auto', p: 3, textAlign: 'center' }}>
        <Typography variant="h6">シナリオを読み込み中...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Paper elevation={2} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom textAlign="center">
          動画のシナリオを選択
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" textAlign="center" mb={4}>
          コンテンツに最適なシナリオテンプレートを選択してください
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
          {scenarios.map((scenario) => {
            const isSelected = selectedScenario === scenario.id;
            
            return (
              <Card 
                key={scenario.id}
                elevation={isSelected ? 8 : 2}
                sx={{ 
                  height: '100%',
                  border: isSelected ? 2 : 0,
                  borderColor: 'primary.main'
                }}
              >
                <CardActionArea onClick={() => onSelect(scenario.id)} sx={{ height: '100%', p: 2 }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      {scenario.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {scenario.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            );
          })}
        </Box>
      </Paper>
    </Box>
  );
}; 