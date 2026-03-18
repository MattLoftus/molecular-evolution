const API_BASE = 'http://localhost:8790';

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${url}`);
  return res.json();
}

export async function fetchStatus() {
  return fetchJson<{
    campaigns: number;
    total_molecules_evaluated: number;
    best_fitness: number;
    best_qed: number;
  }>(`${API_BASE}/api/status`);
}

export async function fetchCampaignList() {
  return fetchJson<Array<{
    name: string;
    config?: Record<string, unknown>;
    generations?: number;
    best_fitness?: number;
    best_qed?: number;
  }>>(`${API_BASE}/api/campaigns`);
}

export async function fetchCampaign(name: string) {
  return fetchJson<{
    name: string;
    config: Record<string, unknown>;
    history: Array<Record<string, unknown>>;
    best_molecule?: Record<string, unknown>;
  }>(`${API_BASE}/api/campaign/${name}`);
}

export async function fetchBestMolecules() {
  return fetchJson<Array<Record<string, unknown>>>(`${API_BASE}/api/best`);
}

export async function fetchKnownDrugs() {
  return fetchJson<Record<string, Record<string, unknown>>>(`${API_BASE}/api/drugs`);
}

export async function fetchAllCampaigns() {
  const list = await fetchCampaignList();
  const campaigns = await Promise.all(
    list.map((c) => fetchCampaign(c.name))
  );
  return campaigns;
}
