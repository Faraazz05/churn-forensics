import { create } from 'zustand'

interface AppState {
  isDemoMode: boolean
  toggleDemoMode: () => void
  isRightPanelOpen: boolean
  rightPanelContent: { type: string; id: string; data?: any } | null
  openRightPanel: (type: string, id: string, data?: any) => void
  closeRightPanel: () => void
}

export const useAppStore = create<AppState>((set) => ({
  isDemoMode: true,
  toggleDemoMode: () => set((state) => ({ isDemoMode: !state.isDemoMode })),
  isRightPanelOpen: false,
  rightPanelContent: null,
  openRightPanel: (type, id, data) => set({ isRightPanelOpen: true, rightPanelContent: { type, id, data } }),
  closeRightPanel: () => set({ isRightPanelOpen: false, rightPanelContent: null }),
}))
