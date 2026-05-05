package top.lally.etime.discipline;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.provider.Settings;

import androidx.core.content.ContextCompat;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "DisciplineMode")
public class DisciplineModePlugin extends Plugin {
    @Override
    public void load() {
        super.load();
        SharedPreferences prefs = DisciplinePrefs.get(getContext());
        if (prefs.getBoolean(DisciplinePrefs.KEY_ENABLED, false)) {
            startMonitorService();
        }
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        call.resolve(buildStatus());
    }

    @PluginMethod
    public void requestUsageAccess(PluginCall call) {
        Intent intent = new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        getContext().startActivity(intent);
        call.resolve(buildStatus());
    }

    @PluginMethod
    public void requestOverlayAccess(PluginCall call) {
        Intent intent = new Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:" + getContext().getPackageName())
        );
        getActivity().startActivity(intent);
        call.resolve(buildStatus());
    }

    @PluginMethod
    public void configure(PluginCall call) {
        Integer limitMinutesValue = call.getInt("limitMinutes");
        String password = call.getString("password");
        int limitMinutes = limitMinutesValue == null ? 0 : limitMinutesValue;

        if (limitMinutes <= 0) {
            call.reject("使用时长必须大于 0 分钟");
            return;
        }

        if (password == null || password.length() < 4) {
            call.reject("解锁密码至少需要 4 位");
            return;
        }

        if (!DisciplineMonitor.hasUsageAccess(getContext())) {
            call.reject("请先授予使用情况访问权限");
            return;
        }

        if (!DisciplineMonitor.hasOverlayPermission(getContext())) {
            call.reject("请先授予悬浮窗权限");
            return;
        }

        SharedPreferences prefs = DisciplinePrefs.get(getContext());
        try {
            DisciplinePrefs.savePassword(prefs, password);
        } catch (Exception e) {
            call.reject("保存解锁密码失败");
            return;
        }

        prefs.edit()
            .putBoolean(DisciplinePrefs.KEY_ENABLED, true)
            .putInt(DisciplinePrefs.KEY_LIMIT_MINUTES, limitMinutes)
            .putLong(DisciplinePrefs.KEY_SUPPRESSED_UNTIL_MS, 0L)
            .apply();

        startMonitorService();
        call.resolve(buildStatus());
    }

    @PluginMethod
    public void disable(PluginCall call) {
        String password = call.getString("password");
        SharedPreferences prefs = DisciplinePrefs.get(getContext());
        if (!DisciplinePrefs.verifyPassword(prefs, password)) {
            call.reject("解锁密码不正确");
            return;
        }

        prefs.edit().putBoolean(DisciplinePrefs.KEY_ENABLED, false).apply();
        DisciplineOverlay.hide(getContext());
        getContext().stopService(new Intent(getContext(), DisciplineService.class));
        call.resolve(buildStatus());
    }

    private JSObject buildStatus() {
        SharedPreferences prefs = DisciplinePrefs.get(getContext());
        boolean enabled = prefs.getBoolean(DisciplinePrefs.KEY_ENABLED, false);
        int limitMinutes = prefs.getInt(DisciplinePrefs.KEY_LIMIT_MINUTES, 0);
        long usageMs = DisciplineMonitor.getTodayUsageMs(getContext());

        JSObject result = new JSObject();
        result.put("supported", true);
        result.put("enabled", enabled);
        result.put("limitMinutes", limitMinutes);
        result.put("usageTodayMinutes", Math.max(0, Math.round(usageMs / 60000.0)));
        result.put("usageAccessGranted", DisciplineMonitor.hasUsageAccess(getContext()));
        result.put("overlayPermissionGranted", DisciplineMonitor.hasOverlayPermission(getContext()));
        result.put("serviceRunning", isServiceRunning());
        result.put("reminderMethod", "overlay");
        return result;
    }

    private void startMonitorService() {
        Intent intent = new Intent(getContext(), DisciplineService.class);
        ContextCompat.startForegroundService(getContext(), intent);
    }

    private boolean isServiceRunning() {
        ActivityManager manager = (ActivityManager) getContext().getSystemService(Context.ACTIVITY_SERVICE);
        if (manager == null) {
            return false;
        }

        for (ActivityManager.RunningServiceInfo service : manager.getRunningServices(Integer.MAX_VALUE)) {
            if (DisciplineService.class.getName().equals(service.service.getClassName())) {
                return true;
            }
        }
        return false;
    }
}
