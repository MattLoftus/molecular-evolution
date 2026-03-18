import { useStore } from '../store';


export default function CampaignSidebar() {
  const campaigns = useStore((s) => s.campaigns);
  const activeIdx = useStore((s) => s.activeCampaignIndex);
  const setActiveIdx = useStore((s) => s.setActiveCampaignIndex);

  if (!campaigns.length) {
    return (
      <div className="w-56 bg-[#0f1923] border-r border-[#1e2d3d] p-3">
        <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
          Campaigns
        </h3>
        <p className="text-xs text-gray-600">No campaigns loaded</p>
      </div>
    );
  }

  return (
    <div className="w-56 bg-[#0f1923] border-r border-[#1e2d3d] p-3 overflow-y-auto">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">
        Campaigns ({campaigns.length})
      </h3>
      <div className="space-y-1">
        {campaigns.map((c, i) => {
          const isActive = i === activeIdx;
          const last = c.history[c.history.length - 1];
          return (
            <button
              key={c.name}
              onClick={() => setActiveIdx(i)}
              className={`w-full text-left px-3 py-2 rounded text-xs transition-colors ${
                isActive
                  ? 'bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981]'
                  : 'hover:bg-[#1a2332] text-gray-400'
              }`}
            >
              <div className="font-medium truncate">{c.name}</div>
              {last && (
                <div className="mt-0.5 text-[10px] text-gray-500">
                  Gen {last.generation + 1} | Fit {last.best_fitness.toFixed(3)} | QED {last.best_qed.toFixed(2)}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
