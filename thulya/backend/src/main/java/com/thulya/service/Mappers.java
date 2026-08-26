package com.thulya.service;

import com.thulya.common.Money;
import com.thulya.domain.Product;
import com.thulya.domain.Review;
import com.thulya.dto.CatalogueDtos.ProductCard;
import com.thulya.dto.CatalogueDtos.ReviewView;

/** Entity -> DTO mapping helpers (money converted paise -> rupees). */
public final class Mappers {

    private Mappers() {}

    public static int discountPct(long mrp, long offer) {
        if (mrp <= 0) return 0;
        return (int) Math.round((1 - (offer / (double) mrp)) * 100);
    }

    public static ProductCard card(Product p) {
        String image = p.getImages().isEmpty() ? null : p.getImages().get(0);
        return new ProductCard(
                p.getId(), p.getSku(), p.getName(), p.getSlug(),
                p.getCategory(), p.getSubCategory(), image,
                Money.paiseToRupees(p.getPriceOffer()),
                Money.paiseToRupees(p.getPriceMrp()),
                discountPct(p.getPriceMrp(), p.getPriceOffer()),
                p.getRatingAvg(), p.getRatingCount(), p.getTags());
    }

    public static ReviewView review(Review r) {
        return new ReviewView(r.getId(), r.getUserName(), r.getRating(), r.getText(),
                r.getImages(), r.isVerifiedPurchase(), r.getCreatedAt());
    }
}
