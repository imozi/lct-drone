export const useElementBounds = (
  container: HTMLElement,
  element: HTMLElement,
): {
  top: number;
  left: number;
  bottom: number;
  right: number;
} => {
  const rectContainer = container.getBoundingClientRect();
  const rectElement = element.getBoundingClientRect();

  const left = rectElement.left - rectContainer.left;
  const right = left + rectElement.width;
  const top = rectElement.top - rectContainer.top;
  const bottom = top + rectElement.height;

  return {
    top,
    left,
    bottom,
    right,
  };
};
