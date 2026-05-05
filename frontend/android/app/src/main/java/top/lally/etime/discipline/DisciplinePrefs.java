package top.lally.etime.discipline;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

final class DisciplinePrefs {
    static final String PREFS_NAME = "discipline_mode";
    static final String KEY_ENABLED = "enabled";
    static final String KEY_LIMIT_MINUTES = "limit_minutes";
    static final String KEY_PASSWORD_HASH = "password_hash";
    static final String KEY_PASSWORD_SALT = "password_salt";
    static final String KEY_PASSWORD_ITERATIONS = "password_iterations";
    static final String KEY_SUPPRESSED_UNTIL_MS = "suppressed_until_ms";

    private static final int SALT_BYTES = 16;
    private static final int PBKDF2_ITERATIONS = 120_000;
    private static final int PBKDF2_BITS = 256;

    private DisciplinePrefs() {}

    static SharedPreferences get(Context context) {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }

    static void savePassword(SharedPreferences prefs, String password) throws Exception {
        byte[] salt = new byte[SALT_BYTES];
        new SecureRandom().nextBytes(salt);
        prefs.edit()
            .putString(KEY_PASSWORD_SALT, Base64.encodeToString(salt, Base64.NO_WRAP))
            .putString(KEY_PASSWORD_HASH, hashPassword(password, salt, PBKDF2_ITERATIONS))
            .putInt(KEY_PASSWORD_ITERATIONS, PBKDF2_ITERATIONS)
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
            int iterations = prefs.getInt(KEY_PASSWORD_ITERATIONS, 0);
            if (iterations > 0) {
                return constantTimeEquals(hashValue, hashPassword(password, salt, iterations));
            }

            boolean legacyMatch = constantTimeEquals(hashValue, legacySha256(password, salt));
            if (legacyMatch) {
                savePassword(prefs, password);
            }
            return legacyMatch;
        } catch (Exception e) {
            return false;
        }
    }

    private static String hashPassword(String password, byte[] salt, int iterations) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, iterations, PBKDF2_BITS);
        try {
            SecretKeyFactory factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
            return Base64.encodeToString(factory.generateSecret(spec).getEncoded(), Base64.NO_WRAP);
        } finally {
            spec.clearPassword();
        }
    }

    private static String legacySha256(String password, byte[] salt) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        digest.update(salt);
        digest.update(password.getBytes(StandardCharsets.UTF_8));
        return Base64.encodeToString(digest.digest(), Base64.NO_WRAP);
    }

    private static boolean constantTimeEquals(String left, String right) {
        if (left == null || right == null) {
            return false;
        }

        byte[] a = left.getBytes(StandardCharsets.UTF_8);
        byte[] b = right.getBytes(StandardCharsets.UTF_8);
        return MessageDigest.isEqual(a, b);
    }
}
