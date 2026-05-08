export type ShareBackgroundStyle = 'vibrant' | 'nature' | 'city' | 'minimal' | 'random';

export interface ShareBackgroundPreset {
  id: string;
  style: Exclude<ShareBackgroundStyle, 'random'>;
  label: string;
  keywords: string[];
  author: string;
  source: string;
  sourceUrl: string;
  imageUrl?: string;
  fallback: string;
  accentColor: string;
  textTone: 'light' | 'dark';
  overlay: string;
}

export const shareBackgroundPresets: ShareBackgroundPreset[] = [
  {
    id: 'vibrant-aurora',
    style: 'vibrant',
    label: '晨光渐变',
    keywords: ['抽象渐变', '活力', '晨光'],
    author: 'ETime',
    source: 'CSS fallback',
    sourceUrl: 'local-css-gradient',
    fallback:
      'radial-gradient(circle at 18% 20%, rgba(255, 214, 111, 0.92), transparent 30%), radial-gradient(circle at 86% 12%, rgba(84, 218, 255, 0.86), transparent 32%), radial-gradient(circle at 44% 82%, rgba(255, 113, 177, 0.82), transparent 34%), linear-gradient(142deg, #3155d4 0%, #7f4fd8 42%, #f96f9b 100%)',
    accentColor: '#ffd36b',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(8, 15, 32, 0.18), rgba(8, 15, 32, 0.64)), radial-gradient(circle at 18% 0%, rgba(255,255,255,0.24), transparent 36%)',
  },
  {
    id: 'vibrant-coral',
    style: 'vibrant',
    label: '珊瑚流光',
    keywords: ['彩色模糊', '流体渐变', '温暖'],
    author: 'ETime',
    source: 'CSS fallback',
    sourceUrl: 'local-css-gradient',
    fallback:
      'radial-gradient(circle at 16% 18%, rgba(255, 239, 160, 0.95), transparent 28%), radial-gradient(circle at 78% 28%, rgba(64, 224, 208, 0.78), transparent 33%), radial-gradient(circle at 34% 78%, rgba(255, 102, 130, 0.88), transparent 36%), linear-gradient(150deg, #173a5e 0%, #5155c8 48%, #ff8a5c 100%)',
    accentColor: '#ffcf6d',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(9, 19, 38, 0.12), rgba(9, 19, 38, 0.68)), radial-gradient(circle at 78% 8%, rgba(255,255,255,0.22), transparent 34%)',
  },
  {
    id: 'nature-ocean',
    style: 'nature',
    label: '海边清晨',
    keywords: ['海边', '阳光', '积极氛围'],
    author: 'Sean Oulashin',
    source: 'Unsplash',
    sourceUrl: 'https://unsplash.com/photos/KMn4VEeEPR8',
    imageUrl:
      'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=85',
    fallback:
      'linear-gradient(180deg, rgba(255, 221, 163, 0.86) 0%, rgba(117, 193, 214, 0.9) 44%, rgba(24, 88, 126, 0.98) 100%)',
    accentColor: '#ffd27a',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(7, 19, 36, 0.08), rgba(7, 19, 36, 0.7)), radial-gradient(circle at 28% 18%, rgba(255, 245, 210, 0.32), transparent 32%)',
  },
  {
    id: 'nature-valley',
    style: 'nature',
    label: '山谷微光',
    keywords: ['山谷', '自然风景', '清晨'],
    author: 'Luca Bravo',
    source: 'Unsplash',
    sourceUrl: 'https://unsplash.com/photos/zAjdgNXsMeg',
    imageUrl:
      'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=85',
    fallback:
      'linear-gradient(180deg, rgba(223, 239, 222, 0.88) 0%, rgba(111, 155, 138, 0.92) 46%, rgba(31, 67, 67, 0.98) 100%)',
    accentColor: '#c8f09c',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(9, 24, 20, 0.16), rgba(9, 24, 20, 0.74)), radial-gradient(circle at 70% 0%, rgba(255,255,255,0.2), transparent 36%)',
  },
  {
    id: 'city-night',
    style: 'city',
    label: '城市夜景',
    keywords: ['城市夜景', '光影', '霓虹'],
    author: 'Pexels',
    source: 'Pexels',
    sourceUrl: 'https://www.pexels.com/search/city%20night/',
    imageUrl:
      'https://images.pexels.com/photos/313782/pexels-photo-313782.jpeg?auto=compress&cs=tinysrgb&w=1200',
    fallback:
      'radial-gradient(circle at 18% 18%, rgba(58, 134, 255, 0.76), transparent 30%), radial-gradient(circle at 88% 32%, rgba(255, 82, 153, 0.74), transparent 28%), linear-gradient(160deg, #07111f 0%, #14213d 52%, #341c46 100%)',
    accentColor: '#7dd3fc',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(3, 8, 18, 0.16), rgba(3, 8, 18, 0.78)), radial-gradient(circle at 80% 12%, rgba(125,211,252,0.22), transparent 36%)',
  },
  {
    id: 'city-pixel-dawn',
    style: 'city',
    label: '像素黎明',
    keywords: ['城市', '清晨', '安静'],
    author: 'Wallhaven community',
    source: 'Local asset',
    sourceUrl: '/img/wallhaven-exd3w8.png',
    imageUrl: '/img/wallhaven-exd3w8.png',
    fallback:
      'linear-gradient(180deg, #f3f7f8 0%, #dfe9ee 50%, #748997 100%)',
    accentColor: '#ffa99c',
    textTone: 'dark',
    overlay:
      'linear-gradient(180deg, rgba(255,255,255,0.12), rgba(255,255,255,0.58)), radial-gradient(circle at 26% 30%, rgba(255, 169, 156, 0.26), transparent 28%)',
  },
  {
    id: 'minimal-glass',
    style: 'minimal',
    label: '玻璃暖光',
    keywords: ['玻璃质感', '极简', '高级'],
    author: 'ETime',
    source: 'CSS fallback',
    sourceUrl: 'local-css-gradient',
    fallback:
      'radial-gradient(circle at 24% 16%, rgba(255, 255, 255, 0.96), transparent 26%), radial-gradient(circle at 84% 18%, rgba(148, 196, 255, 0.44), transparent 30%), radial-gradient(circle at 26% 84%, rgba(235, 179, 120, 0.36), transparent 34%), linear-gradient(150deg, #eef1f4 0%, #d8e3e5 48%, #b9c4c2 100%)',
    accentColor: '#4f7b73',
    textTone: 'dark',
    overlay:
      'linear-gradient(180deg, rgba(255,255,255,0.1), rgba(255,255,255,0.5)), radial-gradient(circle at 50% -12%, rgba(255,255,255,0.28), transparent 38%)',
  },
  {
    id: 'minimal-ink',
    style: 'minimal',
    label: '墨色微光',
    keywords: ['极简高级', '暗色', '克制'],
    author: 'ETime',
    source: 'CSS fallback',
    sourceUrl: 'local-css-gradient',
    fallback:
      'radial-gradient(circle at 78% 8%, rgba(194, 169, 120, 0.34), transparent 28%), radial-gradient(circle at 16% 88%, rgba(96, 165, 250, 0.2), transparent 30%), linear-gradient(155deg, #101418 0%, #22272b 52%, #384038 100%)',
    accentColor: '#d7bd82',
    textTone: 'light',
    overlay:
      'linear-gradient(180deg, rgba(0,0,0,0.04), rgba(0,0,0,0.58)), radial-gradient(circle at 70% 0%, rgba(255,255,255,0.12), transparent 34%)',
  },
];

export const getPresetsByStyle = (style: ShareBackgroundStyle) =>
  style === 'random'
    ? shareBackgroundPresets
    : shareBackgroundPresets.filter((preset) => preset.style === style);

export const getInitialBackgroundPreset = (style: ShareBackgroundStyle) =>
  getPresetsByStyle(style)[0] ?? shareBackgroundPresets[0];
