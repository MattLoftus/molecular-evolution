import { useEffect, useState } from 'react';
import { Analytics } from '@vercel/analytics/react';
import { useStore, useActiveCampaign, useSelectedGenerationData } from './store';
import { fetchAllCampaigns, fetchBestMolecules, fetchKnownDrugs } from './api';
import type { TabId, BestMolecule, Campaign } from './types';
import MoleculeViewer from './components/MoleculeViewer';
import StatsPanel from './components/StatsPanel';
import FitnessCurves from './components/FitnessCurves';
import PropertyRadar from './components/PropertyRadar';
import GenerationSlider from './components/GenerationSlider';
import MoleculeLibrary from './components/MoleculeLibrary';
import CompareView from './components/CompareView';
import CampaignSidebar from './components/CampaignSidebar';
import Guide from './components/Guide';

const TABS: { id: TabId; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'evolution', label: 'Evolution' },
  { id: 'library', label: 'Library' },
  { id: 'compare', label: 'Compare' },
  { id: 'guide', label: 'Guide' },
];

function EmptyState() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setCampaigns = useStore((s) => s.setCampaigns);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;
    setLoading(true);
    setError('');
    try {
      const campaigns: Campaign[] = [];
      for (const file of Array.from(files)) {
        const text = await file.text();
        const data = JSON.parse(text);
        campaigns.push(data as Campaign);
      }
      setCampaigns(campaigns);
    } catch (err) {
      setError(`Failed to parse: ${err}`);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-gray-500">
      <div className="text-6xl mb-4">&#x1F9EC;</div>
      <h2 className="text-xl font-semibold text-gray-300 mb-2">Molecular Evolution Engine</h2>
      <p className="text-sm mb-4">No campaign data loaded. Start the API server or upload results.</p>
      <div className="flex gap-3">
        <label className="cursor-pointer bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] px-4 py-2 rounded text-sm hover:bg-[#10b981]/20 transition-colors">
          Upload Campaign JSON
          <input type="file" accept=".json" multiple onChange={handleFileUpload} className="hidden" />
        </label>
      </div>
      {loading && <p className="text-sm mt-3">Loading...</p>}
      {error && <p className="text-sm mt-3 text-red-400">{error}</p>}
      <p className="text-xs text-gray-600 mt-6">
        Or run: <code className="text-gray-400">python -m engine serve</code> on port 8790
      </p>
    </div>
  );
}

function Dashboard() {
  const campaign = useActiveCampaign();
  const genData = useSelectedGenerationData();
  const selectedGen = useStore((s) => s.selectedGeneration);
  const setSelectedGen = useStore((s) => s.setSelectedGeneration);

  return (
    <div className="space-y-4">
      <StatsPanel campaign={campaign} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          <MoleculeViewer
            molecule={genData?.best_molecule ?? null}
            height="400px"
          />
          <PropertyRadar properties={genData?.best_properties ?? null} />
        </div>
        <div className="space-y-4">
          {campaign && (
            <FitnessCurves
              history={campaign.history}
              selectedGen={selectedGen}
              onSelectGen={setSelectedGen}
            />
          )}
          {campaign && (
            <GenerationSlider
              history={campaign.history}
              selectedGen={selectedGen}
              onSelectGen={setSelectedGen}
            />
          )}
          {genData && (
            <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-2">Best Molecule Details</h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="text-gray-400">
                  SMILES: <span className="text-gray-200 font-mono break-all">{genData.best_molecule.smiles}</span>
                </div>
                <div className="text-gray-400">
                  SELFIES: <span className="text-gray-200 font-mono break-all text-[10px]">{genData.best_molecule.selfies.slice(0, 60)}</span>
                </div>
                <div className="text-gray-400">
                  Heavy atoms: <span className="text-gray-200">{genData.best_properties.num_heavy_atoms}</span>
                </div>
                <div className="text-gray-400">
                  Aromatic rings: <span className="text-gray-200">{genData.best_properties.num_aromatic_rings}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EvolutionView() {
  const campaign = useActiveCampaign();
  const selectedGen = useStore((s) => s.selectedGeneration);
  const setSelectedGen = useStore((s) => s.setSelectedGeneration);
  const genData = useSelectedGenerationData();

  if (!campaign) return <EmptyState />;

  return (
    <div className="space-y-4">
      <GenerationSlider
        history={campaign.history}
        selectedGen={selectedGen}
        onSelectGen={setSelectedGen}
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <MoleculeViewer
          molecule={genData?.best_molecule ?? null}
          height="500px"
        />
        <div className="space-y-4">
          <PropertyRadar properties={genData?.best_properties ?? null} />
          {genData && (
            <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-4">
              <h3 className="text-sm font-medium text-gray-300 mb-3">Generation {genData.generation} Scores</h3>
              <div className="space-y-2">
                {[
                  { label: 'Overall Fitness', value: genData.best_fitness, color: '#10b981' },
                  { label: 'QED (Drug-likeness)', value: genData.best_qed, color: '#3b82f6' },
                  { label: 'SA (Synthesizability)', value: genData.best_sa, color: '#f59e0b' },
                  { label: 'Novelty', value: genData.best_novelty, color: '#8b5cf6' },
                  { label: 'Pop. Diversity', value: genData.population_diversity, color: '#ef4444' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-36">{label}</span>
                    <div className="flex-1 bg-[#0f1923] rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{ width: `${value * 100}%`, backgroundColor: color }}
                      />
                    </div>
                    <span className="text-xs font-mono w-14 text-right" style={{ color }}>
                      {value.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LibraryView() {
  const bestMolecules = useStore((s) => s.bestMolecules);
  const [selected, setSelected] = useState<BestMolecule | null>(null);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <MoleculeLibrary molecules={bestMolecules} onSelect={setSelected} />
        </div>
        <div className="space-y-4">
          <MoleculeViewer molecule={selected?.molecule ?? null} height="300px" />
          {selected && <PropertyRadar properties={selected.properties} />}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const activeTab = useStore((s) => s.activeTab);
  const setActiveTab = useStore((s) => s.setActiveTab);
  const campaigns = useStore((s) => s.campaigns);
  const setCampaigns = useStore((s) => s.setCampaigns);
  const setBestMolecules = useStore((s) => s.setBestMolecules);
  const setKnownDrugs = useStore((s) => s.setKnownDrugs);

  useEffect(() => {
    async function load() {
      try {
        const [allCampaigns, best, drugs] = await Promise.all([
          fetchAllCampaigns(),
          fetchBestMolecules(),
          fetchKnownDrugs(),
        ]);
        setCampaigns(allCampaigns as unknown as Campaign[]);
        setBestMolecules(best as unknown as BestMolecule[]);
        setKnownDrugs(drugs as unknown as Record<string, never>);
      } catch {
        // API not running
      }
    }
    load();
  }, []);

  const hasCampaigns = campaigns.length > 0;

  return (
    <div className="min-h-screen bg-[#0a0f1a] text-[#e8edf5]">
      <header className="bg-[#0f1923] border-b border-[#1e2d3d] px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">&#x1F9EC;</span>
            <h1 className="text-lg font-semibold">Molecular Evolution</h1>
          </div>
          <nav className="flex gap-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 rounded text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#1a2332]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <div className="flex">
        {hasCampaigns && activeTab !== 'guide' && <CampaignSidebar />}
        <main className="flex-1 p-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 56px)' }}>
          {!hasCampaigns && activeTab !== 'guide' ? (
            <EmptyState />
          ) : (
            <>
              {activeTab === 'dashboard' && <Dashboard />}
              {activeTab === 'evolution' && <EvolutionView />}
              {activeTab === 'library' && <LibraryView />}
              {activeTab === 'compare' && <CompareView />}
              {activeTab === 'guide' && <Guide />}
            </>
          )}
        </main>
      </div>
      <Analytics />
    </div>
  );
}
