export const useFormatNumber = (percent: number) => {
  if (percent % 1 !== 0) {
    return Math.trunc(percent * 1000) / 1000;
  }

  return percent;
};
