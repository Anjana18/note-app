package com.thulya.domain;

import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Data
@Document("orders")
public class Order {

    @Id
    private String id;

    @Indexed(unique = true)
    private String orderNo;   // e.g. THU-2048

    @Indexed
    private String userId;

    private String type = "product"; // product | tailoring | mixed
    private List<OrderItem> items = new ArrayList<>();

    private Pricing pricing = new Pricing();
    private Payment payment = new Payment();

    @Indexed
    private OrderStage stage = OrderStage.ORDER_RECEIVED;
    private String assignedTailorId;
    private List<StageEvent> history = new ArrayList<>();
    private Instant expectedReadyAt;

    private String shippingAddressId;
    private Instant createdAt = Instant.now();
    private Instant updatedAt = Instant.now();

    @Data
    public static class OrderItem {
        private String productId;
        private String sku;
        private String name;
        private String size;
        private int qty;
        private long unitPrice;        // paise
        private String tailoringServiceCode; // nullable
        private String measurementId;        // nullable
        private String notes;
    }

    @Data
    public static class Pricing {
        private long subtotal;
        private long discount;
        private long gst;
        private long shipping;
        private long total;
        private String couponCode;
    }

    @Data
    public static class Payment {
        private String status = "pending"; // pending | advance_paid | paid | cod | refunded
        private long advance;
        private long balance;
        private List<String> paymentIds = new ArrayList<>();
    }

    @Data
    public static class StageEvent {
        private OrderStage stage;
        private Instant at = Instant.now();
        private String by;
        private String note;
        private List<String> photos = new ArrayList<>();

        public StageEvent(OrderStage stage, String by) {
            this.stage = stage;
            this.by = by;
        }
    }
}
