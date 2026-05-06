import { toBlob } from 'html-to-image';
import { Capacitor } from '@capacitor/core';

const TARGET_WIDTH = 1080;

export const isNativeShareEnvironment = () => Capacitor.isNativePlatform();

export const renderShareCardBlob = async (node: HTMLElement): Promise<Blob> => {
  if (document.fonts?.ready) {
    await document.fonts.ready;
  }

  const rect = node.getBoundingClientRect();
  const pixelRatio = rect.width > 0 ? TARGET_WIDTH / rect.width : 3;
  const blob = await toBlob(node, {
    cacheBust: true,
    backgroundColor: '#f8fafc',
    pixelRatio,
  });

  if (!blob) {
    throw new Error('生成分享图片失败');
  }

  return blob;
};

export const downloadBlob = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
};

export const blobToObjectUrl = (blob: Blob) => URL.createObjectURL(blob);

export const shareOrDownloadBlob = async (blob: Blob, filename: string, title: string) => {
  const file = new File([blob], filename, { type: 'image/png' });
  const shareData = {
    title,
    text: title,
    files: [file],
  };

  if (navigator.share && navigator.canShare?.(shareData)) {
    await navigator.share(shareData);
    return 'shared' as const;
  }

  // TODO: Add @capacitor/share and @capacitor/filesystem for native save/share
  // once the project chooses to carry those plugins. The fallback below keeps
  // Android and Web buttons responsive without introducing native dependencies.
  downloadBlob(blob, filename);
  return 'downloaded' as const;
};
