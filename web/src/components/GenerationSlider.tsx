import type { GenerationData } from '../types';

export default function GenerationSlider({
  history,
  selectedGen,
  onSelectGen,
}: {
  history: GenerationData[];
  selectedGen: number | null;
  onSelectGen: (gen: number) => void;
}) {
  if (!history.length) return null;

  const maxGen = history[history.length - 1].generation;
  const current = selectedGen ?? maxGen;
  const data = history.find((h) => h.generation === current) ?? history[history.length - 1];

  return (
    <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">Generation</h3>
        <span className="text-lg font-mono text-[#10b981]">{current}</span>
      </div>

      <input
        type="range"
        min={0}
        max={maxGen}
        value={current}
        onChange={(e) => onSelectGen(Number(e.target.value))}
        className="w-full accent-[#10b981]"
      />

      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>0</span>
        <span className="text-gray-400">
          fitness: {data.best_fitness.toFixed(4)} | SMILES: {data.best_molecule.smiles.slice(0, 25)}
          {data.best_molecule.smiles.length > 25 ? '...' : ''}
        </span>
        <span>{maxGen}</span>
      </div>
    </div>
  );
}
