package com.thulya.repository;

import com.thulya.domain.Product;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface ProductRepository extends MongoRepository<Product, String> {
    Optional<Product> findBySlug(String slug);
    Optional<Product> findBySku(String sku);
    Page<Product> findByActiveTrue(Pageable pageable);
    Page<Product> findByActiveTrueAndCategory(String category, Pageable pageable);
    List<Product> findByActiveTrueAndCategoryAndIdNot(String category, String id);
    List<Product> findByStockLessThanEqual(int threshold);
    List<Product> findByTagsContaining(String tag);
}
