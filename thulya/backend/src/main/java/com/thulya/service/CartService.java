package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.common.Money;
import com.thulya.domain.Cart;
import com.thulya.domain.Coupon;
import com.thulya.domain.Product;
import com.thulya.dto.CartDtos.*;
import com.thulya.repository.CartRepository;
import com.thulya.repository.CouponRepository;
import com.thulya.repository.ProductRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class CartService {

    private final CartRepository carts;
    private final ProductRepository products;
    private final CouponRepository coupons;
    private final PricingService pricing;

    public CartService(CartRepository carts, ProductRepository products,
                       CouponRepository coupons, PricingService pricing) {
        this.carts = carts;
        this.products = products;
        this.coupons = coupons;
        this.pricing = pricing;
    }

    private Cart cartFor(String userId) {
        return carts.findByUserId(userId).orElseGet(() -> {
            Cart c = new Cart();
            c.setUserId(userId);
            return c;
        });
    }

    public CartView view(String userId) {
        return toView(cartFor(userId));
    }

    public CartView addItem(String userId, AddItemRequest req) {
        Product p = products.findById(req.productId())
                .orElseThrow(() -> ApiException.notFound("PRODUCT_NOT_FOUND"));
        if (p.getStock() <= 0) throw ApiException.conflict("OUT_OF_STOCK");

        Cart cart = cartFor(userId);
        String size = req.size() != null ? req.size()
                : (p.getSizes().isEmpty() ? "One Size" : p.getSizes().get(0).getLabel());

        cart.getItems().stream()
                .filter(i -> i.getProductId().equals(req.productId()) && size.equals(i.getSize()))
                .findFirst()
                .ifPresentOrElse(
                        i -> i.setQty(i.getQty() + Math.max(1, req.qty())),
                        () -> {
                            Cart.CartItem item = new Cart.CartItem();
                            item.setItemId(UUID.randomUUID().toString());
                            item.setProductId(req.productId());
                            item.setSize(size);
                            item.setQty(Math.max(1, req.qty()));
                            cart.getItems().add(item);
                        });
        cart.setUpdatedAt(Instant.now());
        return toView(carts.save(cart));
    }

    public CartView updateItem(String userId, String itemId, int qty) {
        Cart cart = cartFor(userId);
        cart.getItems().removeIf(i -> i.getItemId().equals(itemId) && qty <= 0);
        cart.getItems().stream().filter(i -> i.getItemId().equals(itemId))
                .forEach(i -> i.setQty(qty));
        return toView(carts.save(cart));
    }

    public CartView removeItem(String userId, String itemId) {
        Cart cart = cartFor(userId);
        cart.getItems().removeIf(i -> i.getItemId().equals(itemId));
        return toView(carts.save(cart));
    }

    public CartView applyCoupon(String userId, String code) {
        Cart cart = cartFor(userId);
        Coupon coupon = coupons.findByCodeAndActiveTrue(code)
                .orElseThrow(() -> ApiException.badRequest("INVALID_COUPON"));
        if (!pricing.isRedeemable(coupon)) throw ApiException.badRequest("COUPON_EXPIRED");
        cart.setCouponCode(code);
        return toView(carts.save(cart));
    }

    private CartView toView(Cart cart) {
        List<CartLine> lines = new ArrayList<>();
        long subtotal = 0;
        for (Cart.CartItem item : cart.getItems()) {
            Product p = products.findById(item.getProductId()).orElse(null);
            if (p == null) continue;
            long line = p.getPriceOffer() * item.getQty();
            subtotal += line;
            String image = p.getImages().isEmpty() ? null : p.getImages().get(0);
            lines.add(new CartLine(item.getItemId(), p.getId(), p.getName(), image,
                    item.getSize(), item.getQty(),
                    Money.paiseToRupees(p.getPriceOffer()), Money.paiseToRupees(line)));
        }

        Coupon coupon = cart.getCouponCode() == null ? null
                : coupons.findByCodeAndActiveTrue(cart.getCouponCode()).orElse(null);
        PricingService.Totals t = pricing.compute(subtotal, coupon);

        return new CartView(lines,
                Money.paiseToRupees(t.subtotal()),
                Money.paiseToRupees(t.discount()),
                Money.paiseToRupees(t.gst()),
                Money.paiseToRupees(t.shipping()),
                Money.paiseToRupees(t.total()),
                cart.getCouponCode());
    }
}
