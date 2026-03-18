import type { Campaign } from '../types';

function StatCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-[#1a2332] rounded-lg p-4 border border-[#1e2d3d]">
      <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-semibold text-[#e8edf5]">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}

export default function StatsPanel({ campaign }: { campaign: Campaign | null }) {
  if (!campaign || !campaign.history.length) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Status" value="No data" />
        <StatCard label="Best Fitness" value="—" />
        <StatCard label="Best QED" value="—" />
        <StatCard label="Molecules" value="—" />
      </div>
    );
  }

  const last = campaign.history[campaign.history.length - 1];
  const totalMols = campaign.config.population_size * campaign.history.length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <StatCard
        label="Generation"
        value={`${last.generation + 1} / ${campaign.config.num_generations}`}
        sub={`${last.elapsed_sec.toFixed(1)}s elapsed`}
      />
      <StatCard
        label="Best Fitness"
        value={last.best_fitness.toFixed(4)}
        sub={`avg: ${last.avg_fitness.toFixed(4)}`}
      />
      <StatCard
        label="Best QED"
        value={last.best_qed.toFixed(3)}
        sub="Drug-likeness (0-1)"
      />
      <StatCard
        label="SA Score"
        value={last.best_sa.toFixed(3)}
        sub="Synthesizability (0-1)"
      />
      <StatCard
        label="Molecules Tested"
        value={totalMols.toLocaleString()}
        sub={`Pop: ${campaign.config.population_size}`}
      />
    </div>
  );
}
