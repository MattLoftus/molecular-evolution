import { useState, useMemo } from 'react';
import MoleculeViewer from './MoleculeViewer';
import PropertyRadar from './PropertyRadar';
import { useStore } from '../store';

export default function CompareView() {
  const bestMolecules = useStore((s) => s.bestMolecules);
  const knownDrugs = useStore((s) => s.knownDrugs);

  const [leftIdx, setLeftIdx] = useState(0);
  const [rightDrug, setRightDrug] = useState<string>('');

  const drugEntries: [string, any][] = useMemo(() => Object.entries(knownDrugs), [knownDrugs]);

  const leftMol = bestMolecules[leftIdx] ?? null;
  const rightMol = rightDrug ? knownDrugs[rightDrug] : null;

  if (!bestMolecules.length) {
    return (
      <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-8 text-center text-gray-500">
        No evolved molecules to compare. Run a campaign first.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {/* Left: Evolved molecule */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-[#10b981]">Evolved</span>
            <select
              className="bg-[#0f1923] text-gray-300 text-xs border border-[#1e2d3d] rounded px-2 py-1 flex-1"
              value={leftIdx}
              onChange={(e) => setLeftIdx(Number(e.target.value))}
            >
              {bestMolecules.map((m, i) => (
                <option key={i} value={i}>
                  #{i + 1} — {m.molecule.smiles.slice(0, 30)} (fitness: {m.fitness.toFixed(4)})
                </option>
              ))}
            </select>
          </div>
          <MoleculeViewer molecule={leftMol?.molecule ?? null} height="350px" />
          {leftMol && <PropertyRadar properties={leftMol.properties} />}
        </div>

        {/* Right: Known drug */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-[#3b82f6]">Known Drug</span>
            <select
              className="bg-[#0f1923] text-gray-300 text-xs border border-[#1e2d3d] rounded px-2 py-1 flex-1"
              value={rightDrug}
              onChange={(e) => setRightDrug(e.target.value)}
            >
              <option value="">Select a drug...</option>
              {drugEntries.map(([id, drug]) => (
                <option key={id} value={id}>
                  {drug.name} — {drug.indication}
                </option>
              ))}
            </select>
          </div>
          {rightMol?.structure ? (
            <>
              <MoleculeViewer molecule={rightMol.structure} height="350px" />
              <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-3 mt-3">
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                  <div>Target: <span className="text-gray-200">{rightMol.target}</span></div>
                  <div>Indication: <span className="text-gray-200">{rightMol.indication}</span></div>
                  <div>MW: <span className="text-gray-200">{rightMol.mw.toFixed(1)}</span></div>
                  <div>Approved: <span className="text-gray-200">{rightMol.approval_year ?? 'N/A'}</span></div>
                  {rightMol.ic50_nM && (
                    <div>IC50: <span className="text-gray-200">{rightMol.ic50_nM} nM</span></div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div
              className="flex items-center justify-center rounded-lg"
              style={{ height: '350px', background: '#0d1420' }}
            >
              <p className="text-gray-500 text-sm">Select a known drug to compare</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
