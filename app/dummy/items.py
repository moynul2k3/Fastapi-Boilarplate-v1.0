import random
from faker import Faker
from tortoise.transactions import in_transaction
from applications.items.items import (
    Category,
    SubCategory,
    SubSubCategory,
    Item,
    ItemImage,
    COLOR_CHOICES,
    SIZE_CHOICES,
)

fake = Faker()

IMAGE_URLS = [
    "https://picsum.photos/600/800",
    "https://picsum.photos/500/700",
    "https://picsum.photos/400/600",
]


# LADIES PRODUCT GENERATORS (FAKER)
MAIN_CATEGORIES = [
    "Ladies Fashion",
    "Beauty & Care",
    "Ladies Accessories",
]

SUBCATEGORY_KEYWORDS = {
    "Ladies Fashion": ["Watch", "Bag", "Dress", "Shoes", "Jewelry"],
    "Beauty & Care": ["Nail", "Makeup", "Skin Care", "Cosmetics"],
    "Ladies Accessories": ["Bracelet", "Hair", "Wallet", "Sunglasses"],
}

PRODUCT_KEYWORDS = {
    "Watch": ["Ladies Watch", "Smart Watch", "Luxury Watch"],
    "Bag": ["Hand Bag", "Shoulder Bag", "Mini Bag"],
    "Jewelry": ["Bracelet", "Necklace", "Earrings"],
    "Nail": ["Nail Polish", "Nail Art Kit", "Gel Nail"],
    "Makeup": ["Lipstick", "Foundation", "Face Powder"],
    "Skin Care": ["Face Cream", "Moisturizer", "Sunscreen"],
    "Hair": ["Hair Clip", "Hair Band", "Scrunchie"],
    "Bracelet": ["Gold Bracelet", "Silver Bracelet"],
}


# MAIN SEED FUNCTION
async def seed_ladies_products(max_items: int = 200):
    print("Seeding ladies products using Faker...")

    created = 0

    for category_name in MAIN_CATEGORIES:
        category, _ = await Category.get_or_create(
            name=category_name,
            defaults={
                "avatar": random.choice(IMAGE_URLS),
                "description": fake.sentence(),
                "popular": True,
            },
        )

        for keyword in SUBCATEGORY_KEYWORDS.get(category_name, []):
            subcategory, _ = await SubCategory.get_or_create(
                category=category,
                name=f"{keyword}s",
                defaults={
                    "avatar": random.choice(IMAGE_URLS),
                    "description": fake.text(120),
                    "popular": True,
                },
            )

            product_names = PRODUCT_KEYWORDS.get(keyword, [keyword])

            for product_base in product_names:
                if created >= max_items:
                    break

                # Faker-powered product name
                product_title = f"{fake.color_name()} {product_base}"

                subsub, _ = await SubSubCategory.get_or_create(
                    subcategory=subcategory,
                    name=product_title,
                    defaults={
                        "avatar": random.choice(IMAGE_URLS),
                        "description": fake.sentence(),
                        "popular": True,
                    },
                )

                async with in_transaction():
                    item = await Item.create(
                        title=product_title,
                        short_bio=fake.text(80),
                        description=fake.text(300),
                        category=category,
                        subcategory=subcategory,
                        sub_subcategory=subsub,
                        ratings=round(random.uniform(3.5, 5.0), 1),
                        box_price=random.randint(800, 15000),
                        total_sale=random.randint(0, 1000),
                        free_delivery=random.choice([True, False]),
                        hot_deals=random.choice([True, False]),
                        flash_sale=random.choice([True, False]),
                        popular=True,
                        brand=fake.company(),
                        warranty=random.choice(
                            ["No Warranty", "6 Months", "1 Year"]
                        ),
                        tag="ladies,fashion,beauty",
                    )

                    # VARIANTS (ItemImage)
                    for _ in range(random.randint(2, 4)):
                        await ItemImage.create(
                            item=item,
                            image=random.choice(IMAGE_URLS),
                            color=random.choice(COLOR_CHOICES)[0],
                            size=random.choice(SIZE_CHOICES)[0],
                            price=random.randint(700, 18000),
                            discount=random.choice([0, 5, 10, 15, 20]),
                            stock=random.randint(5, 150),
                            weight=round(random.uniform(0.1, 3.0), 2),
                            material=random.choice(
                                ["Leather", "Metal", "Plastic", "Fabric", None]
                            ),
                        )

                created += 1

    print(f"Faker ladies seeding complete ({created} items)")
