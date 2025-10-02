import html2canvas from 'html2canvas-pro';

export const exportToImage = async (element: HTMLElement, fileName: string) => {
  try {
    const canvas = await html2canvas(element, {
      useCORS: true,
      allowTaint: true,
      scale: 1,
      logging: false,
      removeContainer: true,
      backgroundColor: '#ffffff',
    });

    const imageUrl = canvas.toDataURL('image/png');

    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `chart-${fileName}-${new Date().toISOString().slice(0, 10)}.png`;

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
  } catch (error) {
    console.error('Ошибка при создании изображения:', error);
  }
};
