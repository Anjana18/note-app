package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.common.Money;
import com.thulya.domain.*;
import com.thulya.dto.OrderDtos.*;
import com.thulya.repository.*;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;

@Service
public class OrderService {

    private final OrderRepository orders;
    private final CartRepository carts;
    private final ProductRepository products;
    private final CouponRepository coupons;
    private final PricingService pricing;
    private final NotificationService notifications;

    public OrderService(OrderRepository orders, CartRepository carts, ProductRepository products,
                        CouponRepository coupons, PricingService pricing, NotificationService notifications) {
        this.orders = orders;
        this.carts = carts;
        this.products = products;
        this.coupons = coupons;
        this.pricing = pricing;
        this.notifications = notifications;
    }

    /** Create an order from the user's current cart. */
    public OrderView createFromCart(String userId, CreateOrderRequest req) {
        Cart cart = carts.findByUserId(userId)
                .orElseThrow(() -> ApiException.badRequest("CART_EMPTY"));
        if (cart.getItems().isEmpty()) throw ApiException.badRequest("CART_EMPTY");

        Order order = new Order();
        order.setOrderNo(nextOrderNo());
        order.setUserId(userId);
        order.setShippingAddressId(req.addressId());

        long subtotal = 0;
        boolean anyTailoring = false;
        for (Cart.CartItem ci : cart.getItems()) {
            Product p = products.findById(ci.getProductId()).orElse(null);
            if (p == null) continue;
            Order.OrderItem oi = new Order.OrderItem();
            oi.setProductId(p.getId());
            oi.setSku(p.getSku());
            oi.setName(p.getName());
            oi.setSize(ci.getSize());
            oi.setQty(ci.getQty());
            oi.setUnitPrice(p.getPriceOffer());
            order.getItems().add(oi);
            subtotal += p.getPriceOffer() * ci.getQty();
            if ("Designer Blouses".equals(p.getCategory()) || p.getTags().contains("stitching")) {
                anyTailoring = true;
            }
        }
        order.setType(anyTailoring ? "mixed" : "product");

        Coupon coupon = cart.getCouponCode() == null ? null
                : coupons.findByCodeAndActiveTrue(cart.getCouponCode()).orElse(null);
        PricingService.Totals t = pricing.compute(subtotal, coupon);

        Order.Pricing pr = order.getPricing();
        pr.setSubtotal(t.subtotal());
        pr.setDiscount(t.discount());
        pr.setGst(t.gst());
        pr.setShipping(t.shipping());
        pr.setTotal(t.total());
        pr.setCouponCode(cart.getCouponCode());

        // Payment kind
        String kind = req.paymentKind() == null ? "full" : req.paymentKind();
        Order.Payment pay = order.getPayment();
        if ("advance".equalsIgnoreCase(kind)) {
            long advance = Money.percentOf(t.total(), 30);
            pay.setStatus("advance_paid");
            pay.setAdvance(advance);
            pay.setBalance(t.total() - advance);
        } else if ("cod".equalsIgnoreCase(kind)) {
            pay.setStatus("cod");
            pay.setBalance(t.total());
        } else {
            pay.setStatus("paid");
            pay.setAdvance(t.total());
        }

        order.getHistory().add(new Order.StageEvent(OrderStage.ORDER_RECEIVED, "system"));
        order.setExpectedReadyAt(Instant.now().plus(7, ChronoUnit.DAYS));
        Order saved = orders.save(order);

        // Clear cart
        cart.getItems().clear();
        cart.setCouponCode(null);
        carts.save(cart);

        notifications.send(userId, "whatsapp", "order_confirmation",
                "Order " + saved.getOrderNo() + " received. Total " + Money.paiseToRupees(t.total()) + " INR.");

        return view(saved);
    }

    public List<OrderView> myOrders(String userId) {
        return orders.findByUserIdOrderByCreatedAtDesc(userId).stream().map(this::view).toList();
    }

    public OrderView get(String orderNo, String userId) {
        Order o = requireOwned(orderNo, userId);
        return view(o);
    }

    public TrackView track(String orderNo) {
        Order o = orders.findByOrderNo(orderNo)
                .orElseThrow(() -> ApiException.notFound("ORDER_NOT_FOUND"));
        List<TimelineStep> steps = new ArrayList<>();
        int current = o.getStage().index();
        for (OrderStage stage : OrderStage.PIPELINE) {
            int idx = stage.index();
            String status = idx < current ? "done" : idx == current ? "active" : "upcoming";
            Order.StageEvent ev = o.getHistory().stream()
                    .filter(e -> e.getStage() == stage).reduce((a, b) -> b).orElse(null);
            steps.add(new TimelineStep(stage.name(), label(stage), status,
                    ev != null ? ev.getAt() : null, ev != null ? ev.getNote() : null));
        }
        return new TrackView(o.getOrderNo(), o.getStage().name(), current,
                o.getAssignedTailorId(), steps);
    }

    /** Admin/Tailor advances (or sets) an order's fulfilment stage. */
    public OrderView updateStage(String orderNo, StageUpdateRequest req, String actorId) {
        Order o = orders.findByOrderNo(orderNo)
                .orElseThrow(() -> ApiException.notFound("ORDER_NOT_FOUND"));
        OrderStage stage;
        try {
            stage = OrderStage.valueOf(req.stage().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw ApiException.badRequest("INVALID_STAGE");
        }
        o.setStage(stage);
        Order.StageEvent ev = new Order.StageEvent(stage, actorId);
        ev.setNote(req.note());
        if (req.photos() != null) ev.setPhotos(req.photos());
        o.getHistory().add(ev);
        o.setUpdatedAt(Instant.now());
        Order saved = orders.save(o);

        String template = stage.notificationTemplate();
        if (template != null) {
            notifications.send(o.getUserId(), "whatsapp", template,
                    "Your order " + o.getOrderNo() + " is now " + label(stage) + ".");
        }
        return view(saved);
    }

    public OrderView assignTailor(String orderNo, String tailorId) {
        Order o = orders.findByOrderNo(orderNo)
                .orElseThrow(() -> ApiException.notFound("ORDER_NOT_FOUND"));
        o.setAssignedTailorId(tailorId);
        return view(orders.save(o));
    }

    public List<OrderView> tailorQueue(String tailorId) {
        return orders.findByAssignedTailorId(tailorId).stream().map(this::view).toList();
    }

    // ---- helpers ----

    private Order requireOwned(String orderNo, String userId) {
        Order o = orders.findByOrderNo(orderNo)
                .orElseThrow(() -> ApiException.notFound("ORDER_NOT_FOUND"));
        if (!o.getUserId().equals(userId)) throw ApiException.notFound("ORDER_NOT_FOUND");
        return o;
    }

    private String nextOrderNo() {
        long n = orders.count() + 2001;
        return "THU-" + n;
    }

    private OrderView view(Order o) {
        List<OrderItemView> items = o.getItems().stream()
                .map(i -> new OrderItemView(i.getProductId(), i.getSku(), i.getName(), i.getSize(),
                        i.getQty(), Money.paiseToRupees(i.getUnitPrice()),
                        i.getTailoringServiceCode(), i.getNotes()))
                .toList();
        Order.Pricing p = o.getPricing();
        PricingView pv = new PricingView(
                Money.paiseToRupees(p.getSubtotal()), Money.paiseToRupees(p.getDiscount()),
                Money.paiseToRupees(p.getGst()), Money.paiseToRupees(p.getShipping()),
                Money.paiseToRupees(p.getTotal()), p.getCouponCode());
        return new OrderView(o.getOrderNo(), o.getType(), items, pv,
                o.getPayment().getStatus(), o.getStage().name(), o.getStage().index(),
                o.getExpectedReadyAt(), o.getCreatedAt());
    }

    private String label(OrderStage stage) {
        String s = stage.name().toLowerCase().replace('_', ' ');
        return Character.toUpperCase(s.charAt(0)) + s.substring(1);
    }
}
