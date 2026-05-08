package top.lally.etime.discipline;

import android.app.ActivityManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.provider.Settings;

import androidx.core.content.ContextCompat;

import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.util.Set;

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
        String scope = call.getString("scope", DisciplinePrefs.SCOPE_ALL);
        JSArray selectedPackagesArray = call.getArray("selectedPackages", new JSArray());
        int limitMinutes = limitMinutesValue == null ? 0 : limitMinutesValue;
        String selectedPackages = normalizeSelectedPackages(selectedPackagesArray);

        if (limitMinutes <= 0) {
            call.reject("使用时长必须大于 0 分钟");
            return;
        }

        if (password == null || password.length() < 4) {
            call.reject("解锁密码至少需要 4 位");
            return;
        }

        if (DisciplinePrefs.SCOPE_SELECTED.equals(scope) && selectedPackages.isEmpty()) {
            call.reject("请至少填写一个要限制的应用包名");
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
            .putString(DisciplinePrefs.KEY_SCOPE, DisciplinePrefs.SCOPE_SELECTED.equals(scope) ? DisciplinePrefs.SCOPE_SELECTED : DisciplinePrefs.SCOPE_ALL)
            .putString(DisciplinePrefs.KEY_SELECTED_PACKAGES, selectedPackages)
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
        String scope = prefs.getString(DisciplinePrefs.KEY_SCOPE, DisciplinePrefs.SCOPE_ALL);
        String selectedPackagesValue = prefs.getString(DisciplinePrefs.KEY_SELECTED_PACKAGES, "");
        Set<String> selectedPackages = DisciplineMonitor.parseSelectedPackages(selectedPackagesValue);
        long usageMs = DisciplinePrefs.SCOPE_SELECTED.equals(scope)
            ? DisciplineMonitor.getTodayUsageMs(getContext(), selectedPackages)
            : DisciplineMonitor.getTodayUsageMs(getContext());

        JSObject result = new JSObject();
        result.put("supported", true);
        result.put("enabled", enabled);
        result.put("limitMinutes", limitMinutes);
        result.put("usageTodayMinutes", Math.max(0, Math.round(usageMs / 60000.0)));
        result.put("usageAccessGranted", DisciplineMonitor.hasUsageAccess(getContext()));
        result.put("overlayPermissionGranted", DisciplineMonitor.hasOverlayPermission(getContext()));
        result.put("serviceRunning", isServiceRunning());
        result.put("scope", DisciplinePrefs.SCOPE_SELECTED.equals(scope) ? DisciplinePrefs.SCOPE_SELECTED : DisciplinePrefs.SCOPE_ALL);
        result.put("selectedPackages", new JSArray(selectedPackages));
        result.put("reminderMethod", "overlay");
        return result;
    }

    private String normalizeSelectedPackages(JSArray selectedPackagesArray) {
        StringBuilder builder = new StringBuilder();
        if (selectedPackagesArray == null) {
            return "";
        }

        for (int i = 0; i < selectedPackagesArray.length(); i++) {
            String packageName = selectedPackagesArray.optString(i, "").trim();
            if (packageName.isEmpty()) {
                continue;
            }
            if (builder.length() > 0) {
                builder.append('\n');
            }
            builder.append(packageName);
        }
        return builder.toString();
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
