import { create } from "zustand";

export const useJobStore = create((set) => ({
  uploadJob: null,
  youtubeJob: null,

  startJob: (id, type) =>
    set((state) => ({
      ...state,
      [`${type}Job`]: {
        id,
        progress: 0,
        result: null,
        isProcessing: true,
      },
    })),

  setProgress: (type, progress) =>
    set((state) => ({
      ...state,
      [`${type}Job`]: {
        ...state[`${type}Job`],
        progress,
      },
    })),

  finishJob: (type, result) =>
    set((state) => ({
      ...state,
      [`${type}Job`]: {
        ...state[`${type}Job`],
        progress: 100,
        result,
        isProcessing: false,
      },
    })),

  clearJob: (type) =>
    set((state) => ({
      ...state,
      [`${type}Job`]: null,
    })),
}));