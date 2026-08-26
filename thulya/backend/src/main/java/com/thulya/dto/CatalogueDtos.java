package com.thulya.dto;

import java.time.Instant;
import java.util.List;

/** Catalogue (category / product / review) response payloads. Money in rupees. */
public final class CatalogueDtos {

    private CatalogueDtos() {}

    public record CategoryView(String id, String name, String slug, String parentId, String icon) {}

    public record ProductCard(
            String id, String sku, String name, String slug,
            String category, String subCategory, String image,
            long priceOffer, long priceMrp, int discountPct,
            double ratingAvg, int ratingCount, List<String> tags) {}

    public record SizeView(String label, int stock) {}

    public record ProductDetail(
            String id, String sku, String name, String slug,
            String category, String subCategory, String description,
            List<String> images, String video,
            String fabric, String washCare, List<SizeView> sizes,
            long priceOffer, long priceMrp, int discountPct, int gstPct,
            String expectedDelivery, int stock, List<String> tags,
            double ratingAvg, int ratingCount, List<ProductCard> related) {}

    public record ReviewView(String id, String userName, int rating, String text,
                             List<String> images, boolean verifiedPurchase, Instant createdAt) {}
}
