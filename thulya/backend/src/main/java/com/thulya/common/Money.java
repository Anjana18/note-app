package com.thulya.common;

/**
 * Money helpers. Amounts are stored internally as integer <b>paise</b> to avoid
 * floating-point rounding; the API boundary exposes whole <b>rupees</b>.
 */
public final class Money {

    private Money() {}

    public static long rupeesToPaise(long rupees) {
        return rupees * 100L;
    }

    /** Convert paise to whole rupees (rounded to nearest rupee). */
    public static long paiseToRupees(long paise) {
        return Math.round(paise / 100.0);
    }

    /** Percentage discount of a paise amount, rounded to nearest paise. */
    public static long percentOf(long paise, int pct) {
        return Math.round(paise * (pct / 100.0));
    }
}
