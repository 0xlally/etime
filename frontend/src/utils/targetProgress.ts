export const TARGET_PROGRESS_CHANGED_EVENT = 'etime:target-progress-changed';

export const notifyTargetProgressChanged = () => {
  window.dispatchEvent(new Event(TARGET_PROGRESS_CHANGED_EVENT));
};
