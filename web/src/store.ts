import { create } from 'zustand';
import type { Campaign, CampaignSummary, BestMolecule, KnownDrug, TabId, GenerationData } from './types';

interface AppState {
  // Data
  campaigns: Campaign[];
  campaignList: CampaignSummary[];
  bestMolecules: BestMolecule[];
  knownDrugs: Record<string, KnownDrug>;

  // UI state
  activeTab: TabId;
  activeCampaignIndex: number;
  selectedGeneration: number | null;
  compareIndices: number[];
  isLive: boolean;

  // Actions
  setActiveTab: (tab: TabId) => void;
  setCampaigns: (campaigns: Campaign[]) => void;
  setCampaignList: (list: CampaignSummary[]) => void;
  addCampaign: (campaign: Campaign) => void;
  setActiveCampaignIndex: (idx: number) => void;
  setSelectedGeneration: (gen: number | null) => void;
  setBestMolecules: (molecules: BestMolecule[]) => void;
  setKnownDrugs: (drugs: Record<string, KnownDrug>) => void;
  toggleCompareIndex: (idx: number) => void;
  setIsLive: (live: boolean) => void;
  appendGeneration: (gen: GenerationData) => void;
}

export const useStore = create<AppState>((set) => ({
  campaigns: [],
  campaignList: [],
  bestMolecules: [],
  knownDrugs: {},
  activeTab: 'dashboard',
  activeCampaignIndex: 0,
  selectedGeneration: null,
  compareIndices: [],
  isLive: false,

  setActiveTab: (tab) => set({ activeTab: tab }),
  setCampaigns: (campaigns) => set({ campaigns }),
  setCampaignList: (list) => set({ campaignList: list }),
  addCampaign: (campaign) =>
    set((s) => ({ campaigns: [...s.campaigns, campaign] })),
  setActiveCampaignIndex: (idx) =>
    set({ activeCampaignIndex: idx, selectedGeneration: null }),
  setSelectedGeneration: (gen) => set({ selectedGeneration: gen }),
  setBestMolecules: (molecules) => set({ bestMolecules: molecules }),
  setKnownDrugs: (drugs) => set({ knownDrugs: drugs }),
  toggleCompareIndex: (idx) =>
    set((s) => {
      const has = s.compareIndices.includes(idx);
      if (has) return { compareIndices: s.compareIndices.filter((i) => i !== idx) };
      if (s.compareIndices.length >= 4) return s;
      return { compareIndices: [...s.compareIndices, idx] };
    }),
  setIsLive: (live) => set({ isLive: live }),
  appendGeneration: (gen) =>
    set((s) => {
      const campaigns = [...s.campaigns];
      if (campaigns.length > 0) {
        const last = { ...campaigns[campaigns.length - 1] };
        last.history = [...last.history, gen];
        campaigns[campaigns.length - 1] = last;
      }
      return { campaigns };
    }),
}));

// Derived selectors
export function useActiveCampaign(): Campaign | null {
  const campaigns = useStore((s) => s.campaigns);
  const idx = useStore((s) => s.activeCampaignIndex);
  return campaigns[idx] ?? null;
}

export function useSelectedGenerationData(): GenerationData | null {
  const campaign = useActiveCampaign();
  const selectedGen = useStore((s) => s.selectedGeneration);
  if (!campaign || !campaign.history.length) return null;
  const gen = selectedGen ?? campaign.history.length - 1;
  return campaign.history[gen] ?? campaign.history[campaign.history.length - 1];
}
