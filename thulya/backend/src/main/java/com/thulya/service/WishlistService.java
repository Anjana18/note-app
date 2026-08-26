package com.thulya.service;

import com.thulya.domain.Wishlist;
import com.thulya.dto.CatalogueDtos.ProductCard;
import com.thulya.repository.ProductRepository;
import com.thulya.repository.WishlistRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
public class WishlistService {

    private final WishlistRepository wishlists;
    private final ProductRepository products;

    public WishlistService(WishlistRepository wishlists, ProductRepository products) {
        this.wishlists = wishlists;
        this.products = products;
    }

    private Wishlist wishFor(String userId) {
        return wishlists.findByUserId(userId).orElseGet(() -> {
            Wishlist w = new Wishlist();
            w.setUserId(userId);
            return w;
        });
    }

    public List<ProductCard> list(String userId) {
        return wishFor(userId).getProductIds().stream()
                .map(products::findById)
                .filter(java.util.Optional::isPresent)
                .map(java.util.Optional::get)
                .map(Mappers::card)
                .toList();
    }

    public List<ProductCard> add(String userId, String productId) {
        Wishlist w = wishFor(userId);
        if (!w.getProductIds().contains(productId)) {
            w.getProductIds().add(productId);
            w.setUpdatedAt(Instant.now());
            wishlists.save(w);
        }
        return list(userId);
    }

    public List<ProductCard> remove(String userId, String productId) {
        Wishlist w = wishFor(userId);
        w.getProductIds().remove(productId);
        w.setUpdatedAt(Instant.now());
        wishlists.save(w);
        return list(userId);
    }
}
