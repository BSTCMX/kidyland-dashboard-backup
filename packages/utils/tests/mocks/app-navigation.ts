/**
 * Mock for $app/navigation
 */
export const goto = (url: string) => {
  // Mock implementation
  if (typeof window !== "undefined") {
    window.location.href = url;
  }
};

export const invalidate = () => Promise.resolve();
export const preloadData = () => Promise.resolve();
export const preloadCode = () => Promise.resolve();
































