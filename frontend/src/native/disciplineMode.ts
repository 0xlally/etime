import { Capacitor, registerPlugin } from '@capacitor/core';

export interface DisciplineStatus {
  supported: boolean;
  enabled: boolean;
  limitMinutes: number;
  usageTodayMinutes: number;
  usageAccessGranted: boolean;
  overlayPermissionGranted: boolean;
  serviceRunning: boolean;
  reminderMethod: 'overlay';
}

interface ConfigureOptions {
  limitMinutes: number;
  password: string;
}

interface DisableOptions {
  password: string;
}

interface DisciplineModePlugin {
  getStatus(): Promise<DisciplineStatus>;
  requestUsageAccess(): Promise<DisciplineStatus>;
  requestOverlayAccess(): Promise<DisciplineStatus>;
  configure(options: ConfigureOptions): Promise<DisciplineStatus>;
  disable(options: DisableOptions): Promise<DisciplineStatus>;
}

const plugin = registerPlugin<DisciplineModePlugin>('DisciplineMode');

const unsupportedStatus: DisciplineStatus = {
  supported: false,
  enabled: false,
  limitMinutes: 0,
  usageTodayMinutes: 0,
  usageAccessGranted: false,
  overlayPermissionGranted: false,
  serviceRunning: false,
  reminderMethod: 'overlay',
};

export const disciplineMode = {
  isAvailable() {
    return Capacitor.isNativePlatform();
  },

  async getStatus() {
    if (!this.isAvailable()) {
      return unsupportedStatus;
    }
    return plugin.getStatus();
  },

  async requestUsageAccess() {
    return plugin.requestUsageAccess();
  },

  async requestOverlayAccess() {
    return plugin.requestOverlayAccess();
  },

  async configure(options: ConfigureOptions) {
    return plugin.configure(options);
  },

  async disable(options: DisableOptions) {
    return plugin.disable(options);
  },
};
