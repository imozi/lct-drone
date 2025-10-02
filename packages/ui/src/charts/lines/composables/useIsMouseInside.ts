export const useIsMouseInside = (
  mouseCoords: { x: number; y: number },
  bounds: {
    top: number;
    left: number;
    bottom: number;
    right: number;
  },
): boolean => {
  const { top, left, bottom, right } = bounds;

  const mouseX = mouseCoords.x;
  const mouseY = mouseCoords.y;

  const isInside = mouseX >= left && mouseX <= right && mouseY >= top && mouseY <= bottom;

  return isInside;
};
