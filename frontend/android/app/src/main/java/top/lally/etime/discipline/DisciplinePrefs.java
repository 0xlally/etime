package top.lally.etime.discipline;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;

import java.security.MessageDigest;
import java.security.SecureRandom;

final class DisciplinePrefs {
    static final String PREFS_NAME = "discipline_mode";
    static final String KEY_ENABLED = "enabled";
    static final String KEY_LIMIT_MINUTES = "limit_minutes";
    static final String KEY_PASSWORD_HASH = "password_hash";
    static final String KEY_PASSWORD_SALT = "password_salt";
    static final String KEY_SUPPRESSED_UNTIL_MS = "suppressed_until_ms";

    private DisciplinePrefs() {}

    static SharedPreferences get(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    static void savePassword(SharedPreferences prefs, String password) throws Exception {
        byte[] salt = new byte[16];
        new SecureRandom().nextBytes(salt);
        prefs.edit()
            .putString(KEY_PASSWORD_SALT, Base64.encodeToString(salt, Base64.NO_WRAP))
            .putString(KEY_PASSWORD_HASH, hashPassword(password, salt))
            .apply();
    }

    static boolean verifyPassword(SharedPreferences prefs, String password) {
        String saltValue = prefs.getString(KEY_PASSWORD_SALT, null);
        String hashValue = prefs.getString(KEY_PASSWORD_HASH, null);
        if (saltValue == null || hashValue == null || password == null) {
            return false;
        }

        try {
            byte[] salt = Base64.decode(saltValue, Base64.NO_WRAP);
            return constantTimeEquals(hashValue, hashPassword(password, salt));
        } catch (Exception e) {
            return false;
        }
    }

    private static String hashPassword(String password, byte[] salt) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        digest.update(salt);
        digest.update(password.getBytes("UTF-8"));
        return Base64.encodeToString(digest.digest(), Base64.NO_WRAP);
    }

    private static boolean constantTimeEquals(String left, String right) {
        if (left == null || right == null) {
            return false;
        }

        byte[] a = left.getBytes();
        byte[] b = right.getBytes();
        int diff = a.length ^ b.length;
        for (int i = 0; i < Math.min(a.length, b.length); i++) {
            diff |= a[i] ^ b[i];
        }
        return diff == 0;
    }
}
