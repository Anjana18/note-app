package com.thulya.service;

import com.thulya.common.Money;
import com.thulya.domain.Coupon;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.time.temporal.ChronoUnit;

import static org.junit.jupiter.api.Assertions.*;

class PricingServiceTest {

    private final PricingService pricing = new PricingService();

    private Coupon percentCoupon(int pct, long maxDiscountRupees, long minOrderRupees) {
        Coupon c = new Coupon();
        c.setCode("THULYA" + pct);
        c.setType("percent");
        c.setValue(pct);
        c.setMaxDiscount(Money.rupeesToPaise(maxDiscountRupees));
        c.setMinOrder(Money.rupeesToPaise(minOrderRupees));
        c.setActive(true);
        c.setStartsAt(Instant.now().minus(1, ChronoUnit.DAYS));
        c.setEndsAt(Instant.now().plus(1, ChronoUnit.DAYS));
        return c;
    }

    @Test
    void computesGstAndTotalWithoutCoupon() {
        long subtotal = Money.rupeesToPaise(10000); // ₹10,000
        PricingService.Totals t = pricing.compute(subtotal, null);
        assertEquals(subtotal, t.subtotal());
        assertEquals(0, t.discount());
        assertEquals(Money.rupeesToPaise(500), t.gst()); // 5% of 10,000
        assertEquals(Money.rupeesToPaise(10500), t.total());
    }

    @Test
    void appliesPercentCouponThenGstOnDiscountedAmount() {
        long subtotal = Money.rupeesToPaise(10000);
        PricingService.Totals t = pricing.compute(subtotal, percentCoupon(10, 0, 1000));
        assertEquals(Money.rupeesToPaise(1000), t.discount());       // 10% of 10,000
        assertEquals(Money.rupeesToPaise(450), t.gst());             // 5% of 9,000
        assertEquals(Money.rupeesToPaise(9450), t.total());
    }

    @Test
    void capsDiscountAtMaxDiscount() {
        long subtotal = Money.rupeesToPaise(30000);
        long discount = pricing.discountFor(subtotal, percentCoupon(10, 1500, 1000)); // 10% = 3000, capped 1500
        assertEquals(Money.rupeesToPaise(1500), discount);
    }

    @Test
    void ignoresCouponBelowMinimumOrder() {
        long subtotal = Money.rupeesToPaise(500);
        long discount = pricing.discountFor(subtotal, percentCoupon(10, 0, 1000));
        assertEquals(0, discount);
    }

    @Test
    void flatCouponSubtractsFixedRupees() {
        Coupon flat = new Coupon();
        flat.setType("flat");
        flat.setValue(200); // ₹200
        flat.setActive(true);
        long discount = pricing.discountFor(Money.rupeesToPaise(2000), flat);
        assertEquals(Money.rupeesToPaise(200), discount);
    }

    @Test
    void expiredCouponIsNotRedeemable() {
        Coupon c = percentCoupon(10, 0, 0);
        c.setEndsAt(Instant.now().minus(1, ChronoUnit.DAYS));
        assertFalse(pricing.isRedeemable(c));
        assertEquals(0, pricing.discountFor(Money.rupeesToPaise(5000), c));
    }

    @Test
    void usageLimitExhaustedIsNotRedeemable() {
        Coupon c = percentCoupon(10, 0, 0);
        c.setUsageLimit(100);
        c.setUsedCount(100);
        assertFalse(pricing.isRedeemable(c));
    }
}
