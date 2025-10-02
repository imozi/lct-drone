type ElementCoords = {
  container: HTMLElement;
  element: HTMLElement;
  centerElement?: boolean;
};

export const useElementCoords = ({ container, element, centerElement = false }: ElementCoords): { x: number; y: number } => {
  const rectContainer = container.getBoundingClientRect();
  const rectElement = element.getBoundingClientRect();

  const coordX = rectElement.x - rectContainer.x;
  const coordY = rectElement.y - rectContainer.y;

  if (centerElement) {
    return {
      x: coordX + rectElement.width / 2,
      y: coordY + rectElement.height / 2,
    };
  }

  return { x: coordX, y: coordY };
};
