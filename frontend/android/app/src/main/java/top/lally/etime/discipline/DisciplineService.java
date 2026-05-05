package top.lally.etime.discipline;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import androidx.core.app.NotificationCompat;

import top.lally.etime.R;

public class DisciplineService extends Service {
    private static final String CHANNEL_ID = "discipline_mode";
    private static final int NOTIFICATION_ID = 1818;
    private static final long CHECK_INTERVAL_MS = 15_000L;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable monitorRunnable = new Runnable() {
        @Override
        public void run() {
            checkDisciplineLimit();
            handler.postDelayed(this, CHECK_INTERVAL_MS);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startForeground(NOTIFICATION_ID, buildNotification());
        handler.removeCallbacks(monitorRunnable);
        handler.post(monitorRunnable);
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(monitorRunnable);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private void checkDisciplineLimit() {
        SharedPreferences prefs = DisciplinePrefs.get(this);
        if (!prefs.getBoolean(DisciplinePrefs.KEY_ENABLED, false)) {
            stopSelf();
            return;
        }

        int limitMinutes = prefs.getInt(DisciplinePrefs.KEY_LIMIT_MINUTES, 0);
        if (limitMinutes <= 0 || !DisciplineMonitor.hasUsageAccess(this) || !DisciplineMonitor.hasOverlayPermission(this)) {
            return;
        }

        long usageMs = DisciplineMonitor.getTodayUsageMs(this);
        if (usageMs < limitMinutes * 60_000L) {
            return;
        }

        long now = System.currentTimeMillis();
        long suppressedUntilMs = prefs.getLong(DisciplinePrefs.KEY_SUPPRESSED_UNTIL_MS, 0L);
        if (now < suppressedUntilMs || DisciplineOverlay.isShowing()) {
            return;
        }

        DisciplineOverlay.show(this, limitMinutes, Math.max(0, Math.round(usageMs / 60000.0)));
    }

    private Notification buildNotification() {
        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle("ETime 自律模式运行中")
            .setContentText("正在统计今日手机使用时长，超限后将显示提醒。")
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }

        NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null || manager.getNotificationChannel(CHANNEL_ID) != null) {
            return;
        }

        NotificationChannel channel = new NotificationChannel(
            CHANNEL_ID,
            "ETime 自律模式",
            NotificationManager.IMPORTANCE_LOW
        );
        channel.setDescription("ETime 自律模式使用时长监控");
        manager.createNotificationChannel(channel);
    }
}
