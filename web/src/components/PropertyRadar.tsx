import Plot from 'react-plotly.js';
import type { MoleculeProperties } from '../types';

export default function PropertyRadar({ properties }: { properties: MoleculeProperties | null }) {
  if (!properties) return null;

  // Normalize properties to 0-1 scale for radar display
  const categories = ['QED', 'SA', 'LogP', 'MW', 'HBD', 'HBA', 'Rings'];
  const values = [
    properties.qed,
    Math.max(0, (10 - properties.sa_score) / 9),  // invert SA
    Math.max(0, Math.min(1, (5 - Math.abs(properties.logp - 2.5)) / 5)),  // ideal ~2.5
    Math.max(0, Math.min(1, 1 - Math.abs(properties.mw - 350) / 350)),    // ideal ~350
    Math.max(0, Math.min(1, 1 - properties.hbd / 5)),      // fewer is better
    Math.max(0, Math.min(1, 1 - properties.hba / 10)),     // fewer is better
    Math.max(0, Math.min(1, properties.num_aromatic_rings / 3)),  // want 1-3
  ];

  // Ideal drug range
  const ideal = [0.7, 0.7, 0.8, 0.8, 0.6, 0.7, 0.7];

  return (
    <div className="bg-[#1a2332] rounded-lg border border-[#1e2d3d] p-3">
      <h3 className="text-sm font-medium text-gray-300 mb-2">Property Profile</h3>
      <Plot
        data={[
          {
            type: 'scatterpolar',
            r: [...ideal, ideal[0]],
            theta: [...categories, categories[0]],
            fill: 'toself',
            fillcolor: 'rgba(59, 130, 246, 0.1)',
            line: { color: 'rgba(59, 130, 246, 0.3)', dash: 'dot' },
            name: 'Ideal range',
          },
          {
            type: 'scatterpolar',
            r: [...values, values[0]],
            theta: [...categories, categories[0]],
            fill: 'toself',
            fillcolor: 'rgba(16, 185, 129, 0.15)',
            line: { color: '#10b981', width: 2 },
            name: 'Current',
          },
        ]}
        layout={{
          polar: {
            bgcolor: 'transparent',
            radialaxis: {
              visible: true,
              range: [0, 1],
              gridcolor: '#1e2d3d',
              tickfont: { color: '#4a5568', size: 9 },
            },
            angularaxis: {
              gridcolor: '#1e2d3d',
              tickfont: { color: '#a0aec0', size: 10 },
            },
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#a0aec0' },
          margin: { l: 40, r: 40, t: 20, b: 40 },
          height: 280,
          showlegend: false,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
      <div className="grid grid-cols-4 gap-2 text-xs text-gray-400 mt-1">
        <div>MW: <span className="text-gray-200">{properties.mw.toFixed(1)}</span></div>
        <div>LogP: <span className="text-gray-200">{properties.logp.toFixed(2)}</span></div>
        <div>HBD: <span className="text-gray-200">{properties.hbd}</span></div>
        <div>HBA: <span className="text-gray-200">{properties.hba}</span></div>
        <div>TPSA: <span className="text-gray-200">{properties.tpsa.toFixed(1)}</span></div>
        <div>RotBonds: <span className="text-gray-200">{properties.rotatable_bonds}</span></div>
        <div>Rings: <span className="text-gray-200">{properties.num_rings}</span></div>
        <div>
          Lipinski:{' '}
          <span className={properties.lipinski_violations === 0 ? 'text-green-400' : 'text-amber-400'}>
            {properties.lipinski_violations === 0 ? 'Pass' : `${properties.lipinski_violations} violation${properties.lipinski_violations > 1 ? 's' : ''}`}
          </span>
        </div>
      </div>
    </div>
  );
}
