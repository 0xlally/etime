package top.lally.etime.discipline;

import android.app.AppOpsManager;
import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.os.Process;
import android.provider.Settings;

import java.util.Calendar;
import java.util.HashMap;
import java.util.Map;

final class DisciplineMonitor {
    private DisciplineMonitor() {}

    static boolean hasUsageAccess(Context context) {
        AppOpsManager appOps = (AppOpsManager) context.getSystemService(Context.APP_OPS_SERVICE);
        if (appOps == null) {
            return false;
        }

        int mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            Process.myUid(),
            context.getPackageName()
        );
        if (mode == AppOpsManager.MODE_DEFAULT) {
            return context.checkCallingOrSelfPermission(android.Manifest.permission.PACKAGE_USAGE_STATS) ==
                android.content.pm.PackageManager.PERMISSION_GRANTED;
        }
        return mode == AppOpsManager.MODE_ALLOWED;
    }

    static boolean hasOverlayPermission(Context context) {
        return Settings.canDrawOverlays(context);
    }

    static long getTodayUsageMs(Context context) {
        UsageStatsManager manager = (UsageStatsManager) context.getSystemService(Context.USAGE_STATS_SERVICE);
        if (manager == null || !hasUsageAccess(context)) {
            return 0L;
        }

        long start = startOfTodayMs();
        long now = System.currentTimeMillis();
        UsageEvents events = manager.queryEvents(start, now);
        UsageEvents.Event event = new UsageEvents.Event();
        Map<String, Long> activeSince = new HashMap<>();
        Map<String, Long> totals = new HashMap<>();
        String ownPackage = context.getPackageName();

        while (events.hasNextEvent()) {
            events.getNextEvent(event);
            String packageName = event.getPackageName();
            if (packageName == null || packageName.equals(ownPackage)) {
                continue;
            }

            int type = event.getEventType();
            if (type == UsageEvents.Event.ACTIVITY_RESUMED || type == UsageEvents.Event.MOVE_TO_FOREGROUND) {
                activeSince.put(packageName, event.getTimeStamp());
            } else if (type == UsageEvents.Event.ACTIVITY_PAUSED || type == UsageEvents.Event.MOVE_TO_BACKGROUND) {
                Long startedAt = activeSince.remove(packageName);
                if (startedAt != null && event.getTimeStamp() > startedAt) {
                    long duration = event.getTimeStamp() - startedAt;
                    Long current = totals.get(packageName);
                    totals.put(packageName, current == null ? duration : current + duration);
                }
            }
        }

        for (Map.Entry<String, Long> entry : activeSince.entrySet()) {
            if (now > entry.getValue()) {
                Long current = totals.get(entry.getKey());
                long duration = now - entry.getValue();
                totals.put(entry.getKey(), current == null ? duration : current + duration);
            }
        }

        long total = 0L;
        for (long duration : totals.values()) {
            total += duration;
        }
        return total;
    }

    private static long startOfTodayMs() {
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, 0);
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        calendar.set(Calendar.MILLISECOND, 0);
        return calendar.getTimeInMillis();
    }
}
