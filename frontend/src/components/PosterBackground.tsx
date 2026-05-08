import React, { useEffect, useState } from 'react';
import { ShareBackgroundPreset } from './shareBackgroundPresets';

interface PosterBackgroundProps {
  preset: ShareBackgroundPreset;
  onLoadStateChange?: (loaded: boolean) => void;
}

export const PosterBackground: React.FC<PosterBackgroundProps> = ({
  preset,
  onLoadStateChange,
}) => {
  const [resolvedImageUrl, setResolvedImageUrl] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const canUseImage = Boolean(resolvedImageUrl) && !imageFailed;

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    setImageLoaded(false);
    setImageFailed(false);
    setResolvedImageUrl(null);

    if (!preset.imageUrl) {
      onLoadStateChange?.(true);
      return () => undefined;
    }

    onLoadStateChange?.(false);

    const resolveImage = async () => {
      try {
        const response = await fetch(preset.imageUrl as string, { cache: 'force-cache' });
        if (!response.ok) throw new Error('poster background fetch failed');
        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setResolvedImageUrl(objectUrl);
        }
      } catch {
        if (!cancelled) {
          setImageFailed(true);
          onLoadStateChange?.(true);
        }
      }
    };

    resolveImage();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [onLoadStateChange, preset.id, preset.imageUrl]);

  const handleLoad = () => {
    setImageLoaded(true);
    onLoadStateChange?.(true);
  };

  const handleError = () => {
    setImageFailed(true);
    setImageLoaded(false);
    onLoadStateChange?.(true);
  };

  return (
    <div className="poster-background" aria-hidden="true">
      <div className="poster-background-fallback" style={{ background: preset.fallback }} />
      {canUseImage && (
        <img
          className={imageLoaded ? 'loaded' : ''}
          src={resolvedImageUrl ?? ''}
          alt=""
          decoding="async"
          onLoad={handleLoad}
          onError={handleError}
        />
      )}
      <div className="poster-background-blur" style={{ background: preset.fallback }} />
      <div className="poster-background-overlay" style={{ background: preset.overlay }} />
      <div className="poster-background-noise" />
      <div className="poster-background-glow" />
    </div>
  );
};
