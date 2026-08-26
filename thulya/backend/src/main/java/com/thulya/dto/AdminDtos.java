package com.thulya.dto;

import com.thulya.dto.CatalogueDtos.ProductCard;

import java.util.List;

public final class AdminDtos {

    private AdminDtos() {}

    public record LowStockView(String id, String sku, String name, int stock) {}

    public record PopularProductView(ProductCard product, int soldEstimate) {}

    public record AnalyticsView(
            long ordersToday, long revenueToday, long bookingsToday,
            long pendingStitching, long completedOrders, long customers,
            List<PopularProductView> popularProducts, List<LowStockView> lowStock) {}
}
