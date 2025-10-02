type AdjustCoordinates = {
  x: number;
  y: number;
  center: number;
  axis: 'x' | 'y';
};

export const useAdjustCoordinates = ({ x, y, center, axis }: AdjustCoordinates): { x: number; y: number } => {
  const adjust = (coordinate: number) => center - (coordinate / 100) * center;

  if (axis === 'x') {
    return { x: adjust(x), y };
  } else {
    return { x, y: adjust(y) };
  }
};
