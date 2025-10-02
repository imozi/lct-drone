export const useThrottle = <T extends (...args: Parameters<T>) => void>(fn: T, wait: number): ((...args: Parameters<T>) => void) => {
  let lastTime = 0;

  return (...args: Parameters<T>): void => {
    const now = Date.now();

    if (now - lastTime >= wait) {
      fn(...args);
      lastTime = now;
    }
  };
};
