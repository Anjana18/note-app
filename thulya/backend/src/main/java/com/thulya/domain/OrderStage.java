package com.thulya.domain;

import java.util.List;

/** The 9-stage tailoring/fulfilment pipeline, in order. */
public enum OrderStage {
    ORDER_RECEIVED,
    MEASUREMENT_COMPLETED,
    CUTTING,
    STITCHING,
    EMBROIDERY,
    QUALITY_CHECK,
    READY,
    DISPATCHED,
    DELIVERED;

    public static final List<OrderStage> PIPELINE = List.of(values());

    public int index() {
        return PIPELINE.indexOf(this);
    }

    /** WhatsApp notification template fired when a stage is reached (null = none). */
    public String notificationTemplate() {
        return switch (this) {
            case READY -> "order_ready";
            case DISPATCHED -> "dispatch_notification";
            case DELIVERED -> "delivery_confirmation";
            default -> null;
        };
    }
}
