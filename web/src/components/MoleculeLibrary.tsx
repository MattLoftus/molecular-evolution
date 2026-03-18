import { useState } from 'react';
import type { BestMolecule } from '../types';

type SortKey = 'fitness' | 'qed' | 'sa' | 'mw' | 'logp' | 'lipinski';

export default function MoleculeLibrary({
  molecules,
  onSelect,
}: {
  molecules: BestMolecule[];
  onSelect?: (mol: BestMolecule) => void;
}) {
  const [sortBy, setSortBy] = useState<SortKey>('fitness');
  const [ascending, setAscending] = useState(false);

  const sorted = [...molecules].sort((a, b) => {
    let va = 0, vb = 0;
    switch (sortBy) {
      case 'fitness': va = a.fitness; vb = b.fitness; break;
      case 'qed': va = a.scores.qed; vb = b.scores.qed; break;
      case 'sa': va = a.scores.sa; vb = b.scores.sa; break;
      case 'mw': va = a.properties.mw; vb = b.properties.mw; break;
      case 'logp': va = a.properties.logp; vb = b.properties.logp; break;
      case 'lipinski': va = a.properties.lipinski_violations; vb = b.properties.lipinski_violations; break;
    }
    return ascending ? va - vb : vb - va;
  });

  const toggleSort = (key: SortKey) => {
    if (sortBy === key) setAscending(!ascending);
    else { setSortBy(key); setAscending(false); }
  };

  const SortHeader = ({ k, label }: { k: SortKey; label: string }) => (
    <th
      className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wider cursor-pointer hover:text-gray-200"
      onClick={() => toggleSort(k)}
    >
      {label} {sortBy === k ? (ascending ? '▲' : '▼') : ''}
    </th>
  );

  if (!molecules.length) {
    return (
      <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-8 text-center text-gray-500">
        No molecules evolved yet. Run a campaign to populate the library.
      </div>
    );
  }

  return (
    <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-[#0f1923]">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase w-8">#</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase">SMILES</th>
              <SortHeader k="fitness" label="Fitness" />
              <SortHeader k="qed" label="QED" />
              <SortHeader k="sa" label="SA" />
              <SortHeader k="mw" label="MW" />
              <SortHeader k="logp" label="LogP" />
              <SortHeader k="lipinski" label="Lipinski" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase">Campaign</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e2d3d]">
            {sorted.map((mol, i) => (
              <tr
                key={i}
                className="hover:bg-[#0f1923] cursor-pointer transition-colors"
                onClick={() => onSelect?.(mol)}
              >
                <td className="px-3 py-2 text-xs text-gray-500">{i + 1}</td>
                <td className="px-3 py-2 text-xs font-mono text-gray-300 max-w-[200px] truncate">
                  {mol.molecule.smiles}
                </td>
                <td className="px-3 py-2 text-sm text-[#10b981] font-medium">
                  {mol.fitness.toFixed(4)}
                </td>
                <td className="px-3 py-2 text-sm text-blue-400">{mol.scores.qed.toFixed(3)}</td>
                <td className="px-3 py-2 text-sm text-amber-400">{mol.scores.sa.toFixed(3)}</td>
                <td className="px-3 py-2 text-xs text-gray-400">{mol.properties.mw.toFixed(1)}</td>
                <td className="px-3 py-2 text-xs text-gray-400">{mol.properties.logp.toFixed(2)}</td>
                <td className="px-3 py-2">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    mol.properties.lipinski_violations === 0
                      ? 'bg-green-900/30 text-green-400'
                      : 'bg-amber-900/30 text-amber-400'
                  }`}>
                    {mol.properties.lipinski_violations === 0 ? 'Pass' : `${mol.properties.lipinski_violations}v`}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs text-gray-500">{mol.campaign || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
