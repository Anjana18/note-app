package com.thulya.service;

import com.thulya.common.ApiException;
import com.thulya.domain.Product;
import com.thulya.dto.CatalogueDtos.*;
import com.thulya.repository.CategoryRepository;
import com.thulya.repository.ProductRepository;
import com.thulya.repository.ReviewRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class CatalogueService {

    private final CategoryRepository categories;
    private final ProductRepository products;
    private final ReviewRepository reviews;

    public CatalogueService(CategoryRepository categories, ProductRepository products, ReviewRepository reviews) {
        this.categories = categories;
        this.products = products;
        this.reviews = reviews;
    }

    public List<CategoryView> categories() {
        return categories.findByActiveTrueOrderByOrderAsc().stream()
                .map(c -> new CategoryView(c.getId(), c.getName(), c.getSlug(), c.getParentId(), c.getIcon()))
                .toList();
    }

    /** Paged product list with optional category filter, text search and sort. */
    public Page<ProductCard> listProducts(String category, String q, String sort, int page, int size) {
        Pageable pageable = PageRequest.of(Math.max(0, page), clamp(size), sortOf(sort));
        Page<Product> result = (category == null || category.isBlank() || category.equalsIgnoreCase("all"))
                ? products.findByActiveTrue(pageable)
                : products.findByActiveTrueAndCategory(category, pageable);

        if (q != null && !q.isBlank()) {
            // Simple in-memory contains filter over the page's dataset for the demo.
            String needle = q.toLowerCase();
            List<ProductCard> filtered = products.findByActiveTrue(PageRequest.of(0, 500, sortOf(sort)))
                    .stream()
                    .filter(p -> (p.getName() + " " + p.getCategory() + " " + p.getSubCategory()).toLowerCase().contains(needle))
                    .map(Mappers::card)
                    .toList();
            int from = Math.min(page * clamp(size), filtered.size());
            int to = Math.min(from + clamp(size), filtered.size());
            return new org.springframework.data.domain.PageImpl<>(
                    filtered.subList(from, to), pageable, filtered.size());
        }
        return result.map(Mappers::card);
    }

    public ProductDetail productDetail(String slugOrId) {
        Product p = products.findBySlug(slugOrId)
                .or(() -> products.findById(slugOrId))
                .orElseThrow(() -> ApiException.notFound("PRODUCT_NOT_FOUND"));

        List<ProductCard> related = products
                .findByActiveTrueAndCategoryAndIdNot(p.getCategory(), p.getId())
                .stream().limit(4).map(Mappers::card).toList();

        List<SizeView> sizes = p.getSizes().stream()
                .map(s -> new SizeView(s.getLabel(), s.getStock())).toList();

        return new ProductDetail(
                p.getId(), p.getSku(), p.getName(), p.getSlug(),
                p.getCategory(), p.getSubCategory(), p.getDescription(),
                p.getImages(), p.getVideo(), p.getFabric(), p.getWashCare(), sizes,
                com.thulya.common.Money.paiseToRupees(p.getPriceOffer()),
                com.thulya.common.Money.paiseToRupees(p.getPriceMrp()),
                Mappers.discountPct(p.getPriceMrp(), p.getPriceOffer()),
                p.getGstPct(),
                p.getDeliveryMinDays() + "–" + p.getDeliveryMaxDays() + " days",
                p.getStock(), p.getTags(), p.getRatingAvg(), p.getRatingCount(), related);
    }

    public List<ProductCard> related(String id) {
        Product p = products.findById(id).orElseThrow(() -> ApiException.notFound("PRODUCT_NOT_FOUND"));
        return products.findByActiveTrueAndCategoryAndIdNot(p.getCategory(), p.getId())
                .stream().limit(6).map(Mappers::card).toList();
    }

    public List<ReviewView> reviews(String productId) {
        return reviews.findByProductIdOrderByCreatedAtDesc(productId).stream()
                .map(Mappers::review).toList();
    }

    private int clamp(int size) {
        if (size <= 0) return 20;
        return Math.min(size, 100);
    }

    private Sort sortOf(String sort) {
        if (sort == null) return Sort.by(Sort.Direction.DESC, "ratingCount");
        return switch (sort) {
            case "new" -> Sort.by(Sort.Direction.DESC, "createdAt");
            case "price_asc" -> Sort.by(Sort.Direction.ASC, "priceOffer");
            case "price_desc" -> Sort.by(Sort.Direction.DESC, "priceOffer");
            default -> Sort.by(Sort.Direction.DESC, "ratingCount"); // popular
        };
    }
}
