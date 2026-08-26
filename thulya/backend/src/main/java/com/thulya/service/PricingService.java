package com.thulya.service;

import com.thulya.common.Money;
import com.thulya.domain.Coupon;
import org.springframework.stereotype.Service;

import java.time.Instant;

/**
 * Pure pricing logic: totals, coupon application and GST. All amounts in paise.
 * Kept free of persistence so it is unit-testable without a database.
 */
@Service
public class PricingService {

    public static final int DEFAULT_GST_PCT = 5;

    /** Immutable pricing breakdown, all fields in paise. */
    public record Totals(long subtotal, long discount, long gst, long shipping, long total) {}

    public Totals compute(long subtotalPaise, Coupon coupon) {
        long discount = discountFor(subtotalPaise, coupon);
        long taxable = Math.max(0, subtotalPaise - discount);
        long gst = Money.percentOf(taxable, DEFAULT_GST_PCT);
        long shipping = 0; // free delivery
        long total = taxable + gst + shipping;
        return new Totals(subtotalPaise, discount, gst, shipping, total);
    }

    /** Discount in paise for a coupon against a subtotal, or 0 if not applicable. */
    public long discountFor(long subtotalPaise, Coupon coupon) {
        if (coupon == null || !isRedeemable(coupon)) return 0;
        if (subtotalPaise < coupon.getMinOrder()) return 0;

        long discount;
        if ("flat".equalsIgnoreCase(coupon.getType())) {
            discount = Money.rupeesToPaise(coupon.getValue());
        } else { // percent
            discount = Money.percentOf(subtotalPaise, coupon.getValue());
        }
        if (coupon.getMaxDiscount() > 0) {
            discount = Math.min(discount, coupon.getMaxDiscount());
        }
        return Math.min(discount, subtotalPaise);
    }

    public boolean isRedeemable(Coupon c) {
        if (c == null || !c.isActive()) return false;
        Instant now = Instant.now();
        if (c.getStartsAt() != null && now.isBefore(c.getStartsAt())) return false;
        if (c.getEndsAt() != null && now.isAfter(c.getEndsAt())) return false;
        if (c.getUsageLimit() > 0 && c.getUsedCount() >= c.getUsageLimit()) return false;
        return true;
    }
}
