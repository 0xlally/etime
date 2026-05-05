package top.lally.etime.discipline;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import top.lally.etime.R;

final class DisciplineOverlay {
    private static final long DISMISS_COOLDOWN_MS = 10 * 60 * 1000L;
    private static View overlayView;

    private DisciplineOverlay() {}

    static boolean isShowing() {
        return overlayView != null;
    }

    static void show(Context context, int limitMinutes, long usageMinutes) {
        if (overlayView != null || !DisciplineMonitor.hasOverlayPermission(context)) {
            return;
        }

        Context appContext = context.getApplicationContext();
        WindowManager windowManager = (WindowManager) appContext.getSystemService(Context.WINDOW_SERVICE);
        if (windowManager == null) {
            return;
        }

        FrameLayout root = new FrameLayout(appContext);

        ImageView background = new ImageView(appContext);
        background.setImageResource(R.drawable.discipline_reminder_bg);
        background.setScaleType(ImageView.ScaleType.CENTER_CROP);
        root.addView(background, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ));

        View scrim = new View(appContext);
        scrim.setBackgroundColor(Color.argb(44, 0, 0, 0));
        root.addView(scrim, new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT
        ));

        LinearLayout container = new LinearLayout(appContext);
        container.setOrientation(LinearLayout.VERTICAL);
        container.setGravity(Gravity.CENTER_HORIZONTAL);
        container.setElevation(dp(appContext, 8));

        LinearLayout reminderPanel = new LinearLayout(appContext);
        reminderPanel.setOrientation(LinearLayout.VERTICAL);
        reminderPanel.setPadding(dp(appContext, 18), dp(appContext, 16), dp(appContext, 18), dp(appContext, 16));
        reminderPanel.setGravity(Gravity.CENTER_HORIZONTAL);

        GradientDrawable panelBackground = new GradientDrawable();
        panelBackground.setColor(Color.argb(188, 17, 24, 39));
        panelBackground.setCornerRadius(dp(appContext, 16));
        reminderPanel.setBackground(panelBackground);

        TextView title = new TextView(appContext);
        title.setText("ETime 自律提醒");
        title.setTextSize(22f);
        title.setTextColor(Color.WHITE);
        title.setGravity(Gravity.CENTER_HORIZONTAL);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);

        TextView body = new TextView(appContext);
        body.setText("今日已用 " + usageMinutes + " 分钟 / 上限 " + limitMinutes + " 分钟\n先向时间认个错，再解锁。");
        body.setTextSize(14f);
        body.setTextColor(Color.rgb(229, 231, 235));
        body.setGravity(Gravity.CENTER_HORIZONTAL);
        body.setPadding(0, dp(appContext, 10), 0, 0);

        EditText passwordInput = new EditText(appContext);
        passwordInput.setHint("解锁密码");
        passwordInput.setHintTextColor(Color.rgb(156, 163, 175));
        passwordInput.setTextColor(Color.WHITE);
        passwordInput.setSingleLine(true);
        passwordInput.setInputType(android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        passwordInput.setGravity(Gravity.CENTER);

        GradientDrawable inputBackground = new GradientDrawable();
        inputBackground.setColor(Color.argb(168, 15, 23, 42));
        inputBackground.setStroke(dp(appContext, 1), Color.argb(190, 251, 191, 36));
        inputBackground.setCornerRadius(dp(appContext, 10));
        passwordInput.setBackground(inputBackground);
        passwordInput.setPadding(dp(appContext, 16), 0, dp(appContext, 16), 0);

        TextView error = new TextView(appContext);
        error.setTextColor(Color.rgb(252, 165, 165));
        error.setTextSize(13f);
        error.setGravity(Gravity.CENTER_HORIZONTAL);
        error.setPadding(0, dp(appContext, 10), 0, 0);

        Button dismissButton = new Button(appContext);
        dismissButton.setText("解锁");
        dismissButton.setAllCaps(false);
        dismissButton.setTextColor(Color.rgb(17, 24, 39));
        dismissButton.setOnClickListener(v -> {
            SharedPreferences prefs = DisciplinePrefs.get(appContext);
            if (!DisciplinePrefs.verifyPassword(prefs, passwordInput.getText().toString())) {
                error.setText("解锁密码不正确");
                return;
            }

            prefs.edit()
                .putLong(DisciplinePrefs.KEY_SUPPRESSED_UNTIL_MS, System.currentTimeMillis() + DISMISS_COOLDOWN_MS)
                .apply();
            hide(appContext);
        });

        reminderPanel.addView(title, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ));
        reminderPanel.addView(body, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ));
        container.addView(reminderPanel, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ));

        LinearLayout unlockRow = new LinearLayout(appContext);
        unlockRow.setOrientation(LinearLayout.HORIZONTAL);

        LinearLayout.LayoutParams inputParams = new LinearLayout.LayoutParams(
            0,
            LinearLayout.LayoutParams.MATCH_PARENT,
            1f
        );
        inputParams.setMargins(0, 0, dp(appContext, 10), 0);
        unlockRow.addView(passwordInput, inputParams);

        unlockRow.addView(dismissButton, new LinearLayout.LayoutParams(
            dp(appContext, 112),
            LinearLayout.LayoutParams.MATCH_PARENT
        ));

        LinearLayout.LayoutParams unlockRowParams = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(appContext, 52)
        );
        unlockRowParams.setMargins(0, dp(appContext, 12), 0, 0);
        container.addView(unlockRow, unlockRowParams);

        container.addView(error, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            dp(appContext, 28)
        ));

        FrameLayout.LayoutParams panelParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT
        );
        panelParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        int panelMargin = dp(appContext, 30);
        panelParams.setMargins(panelMargin, dp(appContext, 46), panelMargin, 0);
        root.addView(container, panelParams);

        WindowManager.LayoutParams params = new WindowManager.LayoutParams(
            WindowManager.LayoutParams.MATCH_PARENT,
            WindowManager.LayoutParams.MATCH_PARENT,
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
            PixelFormat.TRANSLUCENT
        );
        params.gravity = Gravity.CENTER;

        overlayView = root;
        windowManager.addView(root, params);
        passwordInput.requestFocus();
    }

    static void hide(Context context) {
        if (overlayView == null) {
            return;
        }

        WindowManager windowManager = (WindowManager) context.getApplicationContext().getSystemService(Context.WINDOW_SERVICE);
        if (windowManager != null) {
            try {
                windowManager.removeView(overlayView);
            } catch (Exception ignored) {
                // The view may already be detached by the system.
            }
        }
        overlayView = null;
    }

    private static int dp(Context context, int value) {
        float density = context.getResources().getDisplayMetrics().density;
        return Math.round(value * density);
    }
}
