package com.thulya.service;

import com.thulya.common.Money;
import com.thulya.domain.Product;
import com.thulya.dto.CatalogueDtos.ProductCard;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class MappersTest {

    @Test
    void discountPctIsRoundedCorrectly() {
        assertEquals(35, Mappers.discountPct(Money.rupeesToPaise(12999), Money.rupeesToPaise(8499)));
        assertEquals(0, Mappers.discountPct(0, 0));
    }

    @Test
    void cardConvertsPaiseToRupeesAndPicksFirstImage() {
        Product p = new Product();
        p.setId("p1");
        p.setSku("THU-KJV-001");
        p.setName("Kanjivaram Royal Silk");
        p.setSlug("kanjivaram-royal-silk");
        p.setCategory("Sarees");
        p.setSubCategory("Kanjivaram");
        p.setPriceOffer(Money.rupeesToPaise(8499));
        p.setPriceMrp(Money.rupeesToPaise(12999));
        p.setImages(List.of("img1.jpg", "img2.jpg"));
        p.setTags(List.of("new"));

        ProductCard card = Mappers.card(p);
        assertEquals(8499, card.priceOffer());
        assertEquals(12999, card.priceMrp());
        assertEquals(35, card.discountPct());
        assertEquals("img1.jpg", card.image());
        assertEquals("Sarees", card.category());
    }
}
