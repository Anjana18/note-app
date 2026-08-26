package com.thulya.config;

import com.thulya.common.Money;
import com.thulya.domain.*;
import com.thulya.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;

/** Seeds sample catalogue, tailoring pricing, coupon, calendar and demo users on first run. */
@Component
public class DataSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataSeeder.class);

    private final boolean enabled;
    private final CategoryRepository categories;
    private final ProductRepository products;
    private final TailoringServiceRepository tailoring;
    private final CouponRepository coupons;
    private final CalendarConfigRepository calendars;
    private final UserRepository users;

    public DataSeeder(@Value("${thulya.seed.enabled:true}") boolean enabled,
                      CategoryRepository categories, ProductRepository products,
                      TailoringServiceRepository tailoring, CouponRepository coupons,
                      CalendarConfigRepository calendars, UserRepository users) {
        this.enabled = enabled;
        this.categories = categories;
        this.products = products;
        this.tailoring = tailoring;
        this.coupons = coupons;
        this.calendars = calendars;
        this.users = users;
    }

    @Override
    public void run(String... args) {
        if (!enabled) return;
        seedCategories();
        seedProducts();
        seedTailoring();
        seedCoupon();
        seedCalendar();
        seedUsers();
    }

    private void seedCategories() {
        if (categories.count() > 0) return;
        String[][] cats = {
                {"Sarees", "🥻"}, {"Designer Blouses", "👚"}, {"Aari Work", "🪡"},
                {"Lehengas", "👗"}, {"Dress Materials", "🧵"}, {"Readymade Kurtis", "👘"},
                {"Kids Wear", "🧒"}, {"Accessories", "💍"}
        };
        int order = 1;
        for (String[] c : cats) {
            Category cat = new Category();
            cat.setName(c[0]);
            cat.setSlug(c[0].toLowerCase().replace(' ', '-'));
            cat.setIcon(c[1]);
            cat.setOrder(order++);
            categories.save(cat);
        }
        log.info("[seed] categories: {}", categories.count());
    }

    private void seedProducts() {
        if (products.count() > 0) return;
        product("THU-KJV-001", "Kanjivaram Royal Silk", "Sarees", "Kanjivaram", 8499, 12999, 4.9, 214,
                "Pure Mulberry Silk", "Dry clean only", List.of(sz("5.5m", 12)), 12, List.of("new", "trending", "featured"),
                "Handwoven Kanjivaram with contrast zari border and temple pallu — a wedding heirloom.", 3, 5);
        product("THU-ORG-014", "Blush Organza Weave", "Sarees", "Organza", 4299, 6499, 4.7, 98,
                "Organza Silk", "Dry clean", List.of(sz("5.5m", 7)), 7, List.of("sale", "trending", "featured"),
                "Feather-light organza with hand-painted floral motifs and a shimmer gold edge.", 2, 4);
        product("THU-ABL-032", "Peacock Aari Blouse", "Designer Blouses", "Aari Work", 2750, 3900, 5.0, 156,
                "Raw Silk", "Hand wash gentle", List.of(sz("S", 3), sz("M", 5), sz("L", 4), sz("XL", 2)), 14, List.of("featured", "stitching"),
                "Intricate peacock aari embroidery with mirror and bead detailing on the yoke.", 5, 7);
        product("THU-MOD-008", "Modal Silk Everyday", "Sarees", "Modal Silk", 1899, 2499, 4.6, 73,
                "Modal Silk", "Machine wash cold", List.of(sz("5.5m", 20)), 20, List.of("trending"),
                "Buttery-soft modal silk with a subtle sheen — the perfect daily drape.", 2, 3);
        product("THU-AJK-021", "Ajrak Cotton Classic", "Sarees", "Ajrak", 2299, 2999, 4.8, 64,
                "Handblock Cotton", "Hand wash separately", List.of(sz("5.5m", 15)), 15, List.of(),
                "Authentic Ajrak block prints in indigo and madder, naturally dyed.", 3, 5);
        product("THU-LEH-003", "Bridal Velvet Lehenga", "Lehengas", "Bridal", 18999, 26999, 4.9, 41,
                "Velvet + Net", "Dry clean only", List.of(sz("S", 1), sz("M", 1), sz("L", 1)), 3, List.of("new", "featured", "stitching"),
                "Regal velvet lehenga with zardozi and sequin work — the bridal showstopper.", 10, 14);
        product("THU-PBL-011", "Princess-Cut Silk Blouse", "Designer Blouses", "Silk", 1650, 2200, 4.7, 120,
                "Art Silk", "Hand wash", List.of(sz("XS", 2), sz("S", 3), sz("M", 2), sz("L", 1), sz("XL", 1)), 9, List.of("sale", "trending", "stitching"),
                "Tailored princess-cut with piping detail for a flawless silhouette.", 4, 6);
        product("THU-TIS-006", "Tissue Silk Shimmer", "Sarees", "Tissue Silk", 5499, 7999, 4.8, 52,
                "Tissue Silk", "Dry clean", List.of(sz("5.5m", 6)), 6, List.of("featured"),
                "Liquid-gold tissue silk that catches the light with every fold.", 3, 5);
        product("THU-KUR-045", "Ready-to-Wear Kurti", "Readymade Kurtis", "Cotton", 899, 1299, 4.5, 210,
                "Cotton Blend", "Machine wash", List.of(sz("S", 10), sz("M", 12), sz("L", 10), sz("XL", 5), sz("XXL", 3)), 40, List.of("trending"),
                "Breezy A-line kurti with block-print detailing — office to evening.", 1, 2);
        product("THU-KID-017", "Kids Festive Frock", "Kids Wear", "Party", 1199, 1699, 4.9, 88,
                "Cotton Silk", "Hand wash", List.of(sz("2-3y", 5), sz("4-5y", 5), sz("6-7y", 5), sz("8-9y", 3)), 18, List.of("new"),
                "Twirl-worthy festive frock with net overlay and bow detailing.", 2, 4);
        product("THU-LIN-029", "Linen Handloom Saree", "Sarees", "Linen", 2799, 3499, 4.6, 47,
                "Pure Linen", "Dry clean first wash", List.of(sz("5.5m", 11)), 11, List.of(),
                "Crisp handloom linen with contrast temple border — effortless elegance.", 3, 5);
        product("THU-DM-052", "Anarkali Dress Material", "Dress Materials", "Unstitched", 1499, 2099, 4.7, 61,
                "Georgette", "Hand wash", List.of(sz("Unstitched", 22)), 22, List.of("sale"),
                "3-piece Anarkali material with embroidered yoke — stitch to your fit.", 2, 3);
        log.info("[seed] products: {}", products.count());
    }

    private void seedTailoring() {
        if (tailoring.count() > 0) return;
        group("Blouse Stitching", "👚",
                item("blouse_normal", "Normal Blouse", 350, false),
                item("blouse_dart", "Dart Blouse", 650, false),
                item("blouse_princess", "Princess Cut", 750, false),
                item("blouse_designer", "Designer Blouse", 750, true));
        group("Salwar & Anarkali", "👗",
                item("salwar_suit", "Salwar Suit", 900, false),
                item("anarkali", "Anarkali", 1400, true),
                item("patiala", "Patiala Set", 1100, false));
        group("Lehenga & Gown", "💃",
                item("lehenga", "Lehenga", 2500, true),
                item("gown", "Gown", 1800, true),
                item("skirt_fall_pico", "Skirt Fall & Pico", 120, false));
        group("Embroidery & Aari", "🪡",
                item("aari", "Aari Work", 1200, true),
                item("zardozi", "Zardozi", 1800, true),
                item("mirror", "Mirror Work", 900, true));
        group("Kids Dress", "🧒",
                item("kids_frock", "Kids Frock", 600, false),
                item("kids_lehenga", "Kids Lehenga", 900, false),
                item("kids_salwar", "Kids Salwar", 550, false));
        group("Alteration & Add-ons", "✂️",
                item("alteration", "Alteration", 50, false),
                item("blouse_attachment", "Blouse Attachment", 50, false),
                item("fall_edging", "Fall & Edging", 80, false),
                item("hooks_piping", "Hooks & Piping", 60, false));
        log.info("[seed] tailoring groups: {}", tailoring.count());
    }

    private void seedCoupon() {
        if (coupons.count() > 0) return;
        Coupon c = new Coupon();
        c.setCode("THULYA10");
        c.setType("percent");
        c.setValue(10);
        c.setMaxDiscount(Money.rupeesToPaise(1500));
        c.setMinOrder(Money.rupeesToPaise(1000));
        c.setFestival("navratri");
        c.setUsageLimit(1000);
        c.setStartsAt(Instant.now().minus(1, ChronoUnit.DAYS));
        c.setEndsAt(Instant.now().plus(30, ChronoUnit.DAYS));
        coupons.save(c);
        log.info("[seed] coupon THULYA10 created");
    }

    private void seedCalendar() {
        if (calendars.count() > 0) return;
        CalendarConfig cfg = new CalendarConfig();
        for (String d : List.of("mon", "tue", "wed", "thu", "fri", "sat")) {
            cfg.getWorkingHours().put(d, List.of("10:00", "19:00"));
        }
        cfg.setSlotMinutes(60);
        cfg.setMaxPerSlot(3);
        calendars.save(cfg);
        log.info("[seed] calendar config created");
    }

    private void seedUsers() {
        if (users.count() > 0) return;
        demoUser("Divya Ramesh", "+919000000001", Role.CUSTOMER);
        demoUser("Boutique Admin", "+919000000002", Role.ADMIN);
        User priya = demoUser("Priya (Master)", "+919000000003", Role.TAILOR);
        User.TailorProfile tp = new User.TailorProfile();
        tp.setRating(4.9);
        tp.setJobsCompleted(320);
        tp.setSkills(List.of("aari", "zardozi", "bridal"));
        priya.setTailorProfile(tp);
        users.save(priya);
        log.info("[seed] demo users (customer/admin/tailor) created");
    }

    // ---- builders ----

    private User demoUser(String name, String phone, Role role) {
        User u = new User();
        u.setName(name);
        u.setPhone(phone);
        u.setRole(role);
        return users.save(u);
    }

    private Product.Size sz(String label, int stock) {
        return new Product.Size(label, stock);
    }

    private void product(String sku, String name, String category, String sub,
                         long offerRupees, long mrpRupees, double rating, int reviews,
                         String fabric, String wash, List<Product.Size> sizes, int stock,
                         List<String> tags, String desc, int dMin, int dMax) {
        Product p = new Product();
        p.setSku(sku);
        p.setName(name);
        p.setSlug(name.toLowerCase().replaceAll("[^a-z0-9]+", "-").replaceAll("(^-|-$)", ""));
        p.setCategory(category);
        p.setSubCategory(sub);
        p.setPriceOffer(Money.rupeesToPaise(offerRupees));
        p.setPriceMrp(Money.rupeesToPaise(mrpRupees));
        p.setRatingAvg(rating);
        p.setRatingCount(reviews);
        p.setFabric(fabric);
        p.setWashCare(wash);
        p.setSizes(sizes);
        p.setStock(stock);
        p.setTags(tags);
        p.setDescription(desc);
        p.setDeliveryMinDays(dMin);
        p.setDeliveryMaxDays(dMax);
        products.save(p);
    }

    private TailoringService.Item item(String code, String name, long rupees, boolean fromPrice) {
        return new TailoringService.Item(code, name, Money.rupeesToPaise(rupees), fromPrice);
    }

    private void group(String name, String icon, TailoringService.Item... items) {
        TailoringService g = new TailoringService();
        g.setGroup(name);
        g.setIcon(icon);
        g.setItems(List.of(items));
        tailoring.save(g);
    }
}
