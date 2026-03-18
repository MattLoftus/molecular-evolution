"""
HTTP API server for the molecular evolution web dashboard.

Serves campaign results as JSON. Pattern matches antenna-evolution/engine/serve.py.
Port: 8790
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .known_drugs import KNOWN_DRUGS
from .molecule import smiles_to_3d


RESULTS_DIR = Path(__file__).parent.parent / 'results'
PORT = 8790


class CORSHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS and JSON API endpoints."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.rstrip('/')

        if path == '/api/status':
            self._handle_status()
        elif path == '/api/campaigns':
            self._handle_campaigns()
        elif path.startswith('/api/campaign/'):
            name = path.split('/api/campaign/')[1]
            self._handle_campaign(name)
        elif path == '/api/best':
            self._handle_best()
        elif path == '/api/drugs':
            self._handle_drugs()
        else:
            self.send_json({'error': 'Not found'}, 404)

    def _handle_status(self):
        """Summary statistics across all campaigns."""
        campaigns = self._list_campaigns()
        total_molecules = 0
        best_fitness = 0
        best_qed = 0

        for name in campaigns:
            hist_path = RESULTS_DIR / name / 'history.json'
            if hist_path.exists():
                with open(hist_path) as f:
                    history = json.load(f)
                if history:
                    config_path = RESULTS_DIR / name / 'config.json'
                    if config_path.exists():
                        with open(config_path) as f:
                            config = json.load(f)
                        total_molecules += config.get('population_size', 100) * len(history)
                    last = history[-1]
                    best_fitness = max(best_fitness, last.get('best_fitness', 0))
                    best_qed = max(best_qed, last.get('best_qed', 0))

        self.send_json({
            'campaigns': len(campaigns),
            'total_molecules_evaluated': total_molecules,
            'best_fitness': round(best_fitness, 4),
            'best_qed': round(best_qed, 4),
        })

    def _handle_campaigns(self):
        """List all campaigns with summary info."""
        campaigns = []
        for name in self._list_campaigns():
            info = {'name': name}
            config_path = RESULTS_DIR / name / 'config.json'
            if config_path.exists():
                with open(config_path) as f:
                    info['config'] = json.load(f)
            hist_path = RESULTS_DIR / name / 'history.json'
            if hist_path.exists():
                with open(hist_path) as f:
                    history = json.load(f)
                info['generations'] = len(history)
                if history:
                    info['best_fitness'] = history[-1].get('best_fitness', 0)
                    info['best_qed'] = history[-1].get('best_qed', 0)
            campaigns.append(info)
        self.send_json(campaigns)

    def _handle_campaign(self, name: str):
        """Full data for one campaign."""
        campaign_dir = RESULTS_DIR / name
        if not campaign_dir.exists():
            self.send_json({'error': f'Campaign {name} not found'}, 404)
            return

        data = {'name': name}
        for fname in ['config.json', 'history.json', 'best_molecule.json']:
            fpath = campaign_dir / fname
            if fpath.exists():
                with open(fpath) as f:
                    data[fname.replace('.json', '')] = json.load(f)

        self.send_json(data)

    def _handle_best(self):
        """All-time best molecules across all campaigns."""
        best = []
        for name in self._list_campaigns():
            mol_path = RESULTS_DIR / name / 'best_molecule.json'
            if mol_path.exists():
                with open(mol_path) as f:
                    mol_data = json.load(f)
                mol_data['campaign'] = name
                best.append(mol_data)
        best.sort(key=lambda m: m.get('fitness', 0), reverse=True)
        self.send_json(best)

    def _handle_drugs(self):
        """Known reference drugs with 3D structures."""
        drugs = {}
        for drug_id, drug in KNOWN_DRUGS.items():
            entry = dict(drug)
            mol3d = smiles_to_3d(drug['smiles'])
            if mol3d:
                entry['structure'] = mol3d.to_dict()
            drugs[drug_id] = entry
        self.send_json(drugs)

    def _list_campaigns(self):
        """List campaign directories."""
        if not RESULTS_DIR.exists():
            return []
        return sorted([
            d.name for d in RESULTS_DIR.iterdir()
            if d.is_dir() and (d / 'config.json').exists()
        ])

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    """Run the API server."""
    print(f"Molecular Evolution API server on http://localhost:{PORT}")
    print(f"Results directory: {RESULTS_DIR}")
    server = HTTPServer(('', PORT), CORSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == '__main__':
    main()
