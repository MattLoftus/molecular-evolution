import Plot from 'react-plotly.js';
import type { GenerationData } from '../types';

const LAYOUT_BASE: Record<string, unknown> = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  font: { color: '#a0aec0', size: 11 },
  margin: { l: 50, r: 20, t: 30, b: 40 },
  legend: { orientation: 'h', y: -0.15, x: 0.5, xanchor: 'center' },
  xaxis: {
    title: 'Generation',
    gridcolor: '#1e2d3d',
    zerolinecolor: '#1e2d3d',
  },
  yaxis: {
    title: 'Score',
    gridcolor: '#1e2d3d',
    zerolinecolor: '#1e2d3d',
    range: [0, 1],
  },
  hovermode: 'x unified' as const,
};

export default function FitnessCurves({
  history,
  selectedGen,
  onSelectGen,
}: {
  history: GenerationData[];
  selectedGen: number | null;
  onSelectGen: (gen: number) => void;
}) {
  if (!history.length) return null;

  const gens = history.map((h) => h.generation);

  const traces: Record<string, unknown>[] = [
    {
      x: gens,
      y: history.map((h) => h.best_fitness),
      name: 'Fitness',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#10b981', width: 2 },
    },
    {
      x: gens,
      y: history.map((h) => h.avg_fitness),
      name: 'Avg Fitness',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#10b981', width: 1, dash: 'dot' },
    },
    {
      x: gens,
      y: history.map((h) => h.best_qed),
      name: 'QED',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#3b82f6', width: 1.5 },
    },
    {
      x: gens,
      y: history.map((h) => h.best_sa),
      name: 'SA',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#f59e0b', width: 1.5 },
    },
    {
      x: gens,
      y: history.map((h) => h.best_novelty),
      name: 'Novelty',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#8b5cf6', width: 1.5 },
    },
    {
      x: gens,
      y: history.map((h) => h.population_diversity),
      name: 'Diversity',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#ef4444', width: 1, dash: 'dash' },
    },
  ];

  // Selected generation marker
  if (selectedGen !== null) {
    const idx = history.findIndex((h) => h.generation === selectedGen);
    if (idx >= 0) {
      traces.push({
        x: [selectedGen],
        y: [history[idx].best_fitness],
        type: 'scatter',
        mode: 'markers',
        marker: { color: '#10b981', size: 12, symbol: 'diamond' },
        showlegend: false,
        hoverinfo: 'skip',
      });
    }
  }

  return (
    <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-3">
      <h3 className="text-sm font-medium text-gray-300 mb-2">Fitness Over Generations</h3>
      <Plot
        data={traces}
        layout={{
          ...LAYOUT_BASE,
          height: 300,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
        onClick={(data: { points: Array<{ x: number }> }) => {
          if (data.points.length > 0) {
            onSelectGen(data.points[0].x as number);
          }
        }}
      />
    </div>
  );
}
