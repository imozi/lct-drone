type MouseCoords = {
  evt: MouseEvent;
  container: HTMLElement;
};

export const useMouseCoords = ({ evt, container }: MouseCoords): { x: number; y: number } => {
  const rectContainer = container.getBoundingClientRect();
  const coordX = evt.x - rectContainer.x;
  const coordY = evt.y - rectContainer.y;

  return { x: coordX, y: coordY };
};
