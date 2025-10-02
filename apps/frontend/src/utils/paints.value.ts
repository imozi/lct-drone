export const paints = (value: number) => {
  if (value >= 75) {
    return 'bg-[#B0DA86]';
  }

  if (value >= 50 && value <= 74) {
    return 'bg-[#D7EDC2]';
  }

  if (value >= 25 && value <= 49) {
    return 'bg-[#FFE2E2]';
  }

  return 'bg-[#F59E9E]';
};
