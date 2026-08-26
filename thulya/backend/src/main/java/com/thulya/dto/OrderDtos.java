package com.thulya.dto;

import jakarta.validation.constraints.NotBlank;

import java.time.Instant;
import java.util.List;

/** Order + tracking payloads. Money in rupees. */
public final class OrderDtos {

    private OrderDtos() {}

    public record CreateOrderRequest(String addressId, String paymentKind) {} // full | advance | cod

    public record OrderItemView(String productId, String sku, String name, String size,
                                int qty, long unitPrice, String tailoringServiceCode, String notes) {}

    public record PricingView(long subtotal, long discount, long gst, long shipping,
                              long total, String couponCode) {}

    public record OrderView(String orderNo, String type, List<OrderItemView> items,
                            PricingView pricing, String paymentStatus, String stage,
                            int stageIndex, Instant expectedReadyAt, Instant createdAt) {}

    public record StageUpdateRequest(@NotBlank String stage, String note, List<String> photos) {}

    public record AssignTailorRequest(@NotBlank String tailorId) {}

    public record TimelineStep(String stage, String label, String status, Instant at, String note) {}

    public record TrackView(String orderNo, String stage, int stageIndex,
                            String assignedTailorId, List<TimelineStep> timeline) {}
}
