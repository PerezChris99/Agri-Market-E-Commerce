"""
Management command to populate Uganda delivery zones and sample data.

Usage:
    python manage.py populate_uganda_data
    python manage.py populate_uganda_data --zones-only
    python manage.py populate_uganda_data --products-only
"""

from django.core.management.base import BaseCommand
from store.models import DeliveryZone, Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate Uganda delivery zones and sample agricultural products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--zones-only',
            action='store_true',
            help='Only populate delivery zones',
        )
        parser.add_argument(
            '--products-only',
            action='store_true',
            help='Only populate sample products',
        )

    def handle(self, *args, **options):
        zones_only = options.get('zones_only', False)
        products_only = options.get('products_only', False)
        
        if not products_only:
            self.populate_delivery_zones()
        
        if not zones_only:
            self.populate_categories()
            self.populate_products()
        
        self.stdout.write(self.style.SUCCESS('✅ Uganda data populated successfully!'))

    def populate_delivery_zones(self):
        """Populate all Uganda districts as delivery zones"""
        self.stdout.write('Populating delivery zones...')
        
        # Uganda Regions and their districts
        uganda_zones = {
            'Central Region': {
                'delivery_fee': 5000,
                'districts': [
                    ('Kampala', 3000),  # Capital gets lower fee
                    ('Wakiso', 5000),
                    ('Mukono', 6000),
                    ('Mpigi', 7000),
                    ('Masaka', 10000),
                    ('Luwero', 8000),
                    ('Mityana', 9000),
                    ('Mubende', 12000),
                    ('Nakaseke', 10000),
                    ('Nakasongola', 12000),
                    ('Rakai', 12000),
                    ('Sembabule', 11000),
                    ('Kayunga', 8000),
                    ('Buikwe', 7000),
                    ('Buvuma', 15000),
                    ('Gomba', 10000),
                    ('Kalungu', 10000),
                    ('Butambala', 8000),
                    ('Kalangala', 20000),  # Island - higher fee
                    ('Kyotera', 12000),
                    ('Lwengo', 11000),
                ]
            },
            'Eastern Region': {
                'delivery_fee': 12000,
                'districts': [
                    ('Jinja', 10000),
                    ('Mbale', 15000),
                    ('Soroti', 18000),
                    ('Tororo', 14000),
                    ('Busia', 15000),
                    ('Iganga', 12000),
                    ('Kamuli', 14000),
                    ('Kumi', 16000),
                    ('Pallisa', 16000),
                    ('Budaka', 15000),
                    ('Bukedea', 16000),
                    ('Bukwo', 20000),
                    ('Bulambuli', 18000),
                    ('Busia', 15000),
                    ('Kaberamaido', 17000),
                    ('Kapchorwa', 20000),
                    ('Katakwi', 18000),
                    ('Manafwa', 17000),
                    ('Mayuge', 12000),
                    ('Namutumba', 14000),
                    ('Sironko', 17000),
                    ('Bududa', 18000),
                    ('Butaleja', 15000),
                    ('Buyende', 15000),
                    ('Kaliro', 14000),
                    ('Kibuku', 16000),
                    ('Kween', 20000),
                    ('Luuka', 14000),
                    ('Namayingo', 14000),
                    ('Ngora', 16000),
                    ('Serere', 16000),
                ]
            },
            'Northern Region': {
                'delivery_fee': 18000,
                'districts': [
                    ('Gulu', 18000),
                    ('Lira', 16000),
                    ('Arua', 22000),
                    ('Kitgum', 22000),
                    ('Apac', 17000),
                    ('Nebbi', 22000),
                    ('Pader', 22000),
                    ('Adjumani', 23000),
                    ('Moyo', 24000),
                    ('Yumbe', 25000),
                    ('Amolatar', 18000),
                    ('Amuru', 20000),
                    ('Dokolo', 17000),
                    ('Nwoya', 20000),
                    ('Oyam', 17000),
                    ('Abim', 25000),
                    ('Agago', 22000),
                    ('Alebtong', 18000),
                    ('Amudat', 28000),
                    ('Kaabong', 28000),
                    ('Kole', 17000),
                    ('Kotido', 27000),
                    ('Lamwo', 24000),
                    ('Moroto', 26000),
                    ('Nakapiripirit', 26000),
                    ('Napak', 26000),
                    ('Otuke', 19000),
                    ('Zombo', 23000),
                    ('Koboko', 25000),
                    ('Maracha', 24000),
                ]
            },
            'Western Region': {
                'delivery_fee': 15000,
                'districts': [
                    ('Mbarara', 14000),
                    ('Fort Portal', 16000),
                    ('Kabale', 18000),
                    ('Kasese', 17000),
                    ('Hoima', 15000),
                    ('Masindi', 16000),
                    ('Bushenyi', 15000),
                    ('Ntungamo', 16000),
                    ('Rukungiri', 17000),
                    ('Ibanda', 15000),
                    ('Isingiro', 16000),
                    ('Kamwenge', 17000),
                    ('Kanungu', 19000),
                    ('Kiruhura', 15000),
                    ('Kyenjojo', 16000),
                    ('Bundibugyo', 22000),
                    ('Buliisa', 18000),
                    ('Kibaale', 17000),
                    ('Kiryandongo', 16000),
                    ('Kyegegwa', 16000),
                    ('Mitooma', 17000),
                    ('Ntoroko', 20000),
                    ('Rubirizi', 18000),
                    ('Sheema', 15000),
                    ('Buhweju', 17000),
                    ('Kagadi', 17000),
                    ('Kakumiro', 17000),
                    ('Rubanda', 19000),
                    ('Rukiga', 18000),
                ]
            }
        }
        
        created_count = 0
        updated_count = 0
        
        region_values = {
            'Central Region': 'central',
            'Eastern Region': 'eastern',
            'Northern Region': 'northern',
            'Western Region': 'western',
        }
        for region, data in uganda_zones.items():
            region_value = region_values[region]
            for district, fee in data['districts']:
                zone_name = f"{district}, {region}"
                zone, created = DeliveryZone.objects.update_or_create(
                    name=zone_name,
                    defaults={
                        'region': region_value,
                        'delivery_fee': Decimal(str(fee)),
                        'estimated_days': self._get_delivery_days(region),
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        
        self.stdout.write(f'  Created {created_count} zones, updated {updated_count} zones')

    def _get_delivery_days(self, region):
        """Get estimated delivery days based on region"""
        delivery_times = {
            'Central Region': 1,
            'Eastern Region': 2,
            'Northern Region': 3,
            'Western Region': 2,
        }
        return delivery_times.get(region, 3)

    def populate_categories(self):
        """Populate agricultural product categories"""
        self.stdout.write('Populating categories...')
        
        categories = [
            ('Fresh Fruits', 'fresh-fruits', 'Fresh and ripe fruits from Ugandan farms'),
            ('Vegetables', 'vegetables', 'Farm-fresh vegetables and greens'),
            ('Grains & Cereals', 'grains-cereals', 'Rice, maize, millet, sorghum and more'),
            ('Legumes & Pulses', 'legumes-pulses', 'Beans, groundnuts, soybeans'),
            ('Roots & Tubers', 'roots-tubers', 'Cassava, sweet potatoes, Irish potatoes'),
            ('Dairy & Eggs', 'dairy-eggs', 'Fresh milk, ghee, eggs from local farms'),
            ('Poultry & Meat', 'poultry-meat', 'Chicken, beef, goat meat, pork'),
            ('Fish & Seafood', 'fish-seafood', 'Fresh fish from Lake Victoria and fish farms'),
            ('Herbs & Spices', 'herbs-spices', 'Local herbs, spices, and seasonings'),
            ('Honey & Bee Products', 'honey-bee-products', 'Pure honey, propolis, bee wax'),
            ('Coffee & Tea', 'coffee-tea', 'Uganda\'s finest arabica and robusta coffee'),
            ('Oil Seeds', 'oil-seeds', 'Sunflower, simsim, palm oil'),
        ]
        
        created_count = 0
        for name, slug, description in categories:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'  Created {created_count} categories')

    def populate_products(self):
        """Populate sample agricultural products"""
        self.stdout.write('Populating sample products...')
        
        products_data = [
            # Fresh Fruits
            ('fresh-fruits', [
                ('Fresh Mangoes (1kg)', 'fresh-mangoes', 8000, 'Sweet and juicy mangoes from Eastern Uganda. Perfect ripeness guaranteed.', 50),
                ('Organic Bananas (Bunch)', 'organic-bananas', 5000, 'Organically grown matooke bananas. Green cooking bananas from Bushenyi.', 100),
                ('Watermelon (Large)', 'watermelon-large', 12000, 'Sweet red watermelons from Karamoja. Perfect for the hot weather.', 30),
                ('Passion Fruits (1kg)', 'passion-fruits', 10000, 'Fresh passion fruits, perfect for juice. Rich in vitamin C.', 40),
                ('Pineapples (Large)', 'pineapples-large', 6000, 'Sweet and tangy pineapples from Kayunga. Export quality.', 60),
                ('Avocados (4pcs)', 'avocados-pack', 8000, 'Creamy Hass avocados. Rich in healthy fats and nutrients.', 45),
                ('Oranges (1kg)', 'oranges-kg', 4000, 'Juicy oranges from Teso region. Fresh and vitamin-rich.', 80),
                ('Papaya (Medium)', 'papaya-medium', 5000, 'Ripe pawpaws, sweet and nutritious. Great for digestion.', 35),
            ]),
            # Vegetables
            ('vegetables', [
                ('Fresh Tomatoes (1kg)', 'fresh-tomatoes', 4000, 'Ripe red tomatoes, perfect for cooking. Locally grown.', 100),
                ('Green Peppers (500g)', 'green-peppers', 3500, 'Crunchy green peppers, great for salads and stir-fry.', 60),
                ('Onions (1kg)', 'onions-kg', 5000, 'Quality onions from Kaberamaido. Long-lasting freshness.', 150),
                ('Cabbage (Large Head)', 'cabbage-large', 3000, 'Fresh green cabbage. Great for coleslaw and cooking.', 80),
                ('Eggplants (Biringanya) 1kg', 'eggplants-kg', 4500, 'Fresh African eggplants. Traditional variety.', 45),
                ('Sukuma Wiki (Bundle)', 'sukuma-wiki', 2000, 'Fresh collard greens, locally called sukuma wiki.', 100),
                ('Carrots (500g)', 'carrots-500g', 3000, 'Fresh carrots, great for salads and cooking.', 70),
                ('Nakati (Bundle)', 'nakati-bundle', 2500, 'Traditional Ugandan greens, rich in iron.', 90),
            ]),
            # Grains & Cereals
            ('grains-cereals', [
                ('Maize Flour (5kg)', 'maize-flour-5kg', 18000, 'Freshly milled posho flour. Premium quality.', 100),
                ('Rice (5kg) - Super', 'rice-super-5kg', 28000, 'Ugandan super rice from Doho. Long grain premium.', 80),
                ('Millet Flour (2kg)', 'millet-flour-2kg', 12000, 'Finger millet flour for porridge. Nutritious breakfast.', 50),
                ('Sorghum (2kg)', 'sorghum-2kg', 8000, 'Red sorghum grains. Great for local beer and porridge.', 45),
                ('Maize (Dried) 5kg', 'dried-maize-5kg', 15000, 'Quality dried maize for animal feed or milling.', 200),
            ]),
            # Legumes & Pulses
            ('legumes-pulses', [
                ('Beans (Nambale) 2kg', 'beans-nambale-2kg', 14000, 'Red kidney beans from Nambale. High protein content.', 80),
                ('Groundnuts (1kg)', 'groundnuts-1kg', 10000, 'Roasted groundnuts, ready to eat or cook.', 60),
                ('Soya Beans (2kg)', 'soya-beans-2kg', 16000, 'Organic soya beans. Great for plant protein.', 40),
                ('Green Grams (Ndengu) 1kg', 'green-grams-1kg', 8000, 'Mung beans/ndengu. Popular for curry dishes.', 55),
                ('Cowpeas (1kg)', 'cowpeas-1kg', 7000, 'Traditional cowpeas, rich in fiber and protein.', 65),
            ]),
            # Roots & Tubers
            ('roots-tubers', [
                ('Cassava (Fresh) 5kg', 'cassava-fresh-5kg', 10000, 'Fresh cassava roots from Western Uganda. Ready to cook.', 60),
                ('Sweet Potatoes (5kg)', 'sweet-potatoes-5kg', 12000, 'Orange-fleshed sweet potatoes. Rich in vitamin A.', 70),
                ('Irish Potatoes (5kg)', 'irish-potatoes-5kg', 20000, 'Fresh Irish potatoes from Kabale. Perfect for fries.', 50),
                ('Cassava Flour (2kg)', 'cassava-flour-2kg', 8000, 'Fine cassava flour for baking and cooking.', 45),
                ('Yams (2kg)', 'yams-2kg', 15000, 'Fresh yams, great for roasting and boiling.', 30),
            ]),
            # Dairy & Eggs
            ('dairy-eggs', [
                ('Fresh Eggs (Tray 30)', 'eggs-tray-30', 15000, 'Farm-fresh eggs from free-range chickens.', 100),
                ('Fresh Milk (1L)', 'fresh-milk-1l', 3500, 'Fresh cow\'s milk from Mbarara farms.', 50),
                ('Local Ghee (500ml)', 'local-ghee-500ml', 25000, 'Traditional ghee made from fresh butterfat.', 30),
                ('Yogurt (500ml)', 'yogurt-500ml', 5000, 'Natural yogurt, locally made. No preservatives.', 40),
            ]),
            # Poultry & Meat
            ('poultry-meat', [
                ('Whole Chicken (Kienyeji)', 'chicken-kienyeji', 35000, 'Free-range local chicken. Tender and flavorful.', 30),
                ('Beef (1kg)', 'beef-1kg', 18000, 'Fresh beef from grass-fed cattle. Premium cut.', 40),
                ('Goat Meat (1kg)', 'goat-meat-1kg', 22000, 'Fresh goat meat, locally sourced. Great for stew.', 25),
                ('Pork (1kg)', 'pork-1kg', 16000, 'Fresh pork from healthy pigs. For roasting or stew.', 35),
            ]),
            # Fish & Seafood
            ('fish-seafood', [
                ('Tilapia (Fresh) 1kg', 'tilapia-fresh-1kg', 20000, 'Fresh tilapia from Lake Victoria. Cleaned and ready.', 40),
                ('Nile Perch (1kg)', 'nile-perch-1kg', 25000, 'Fresh Nile Perch fillets. Premium lake fish.', 30),
                ('Dried Fish (Mukene) 500g', 'mukene-500g', 12000, 'Small dried silver fish. Rich in calcium.', 50),
                ('Catfish (1kg)', 'catfish-1kg', 18000, 'Farm-raised catfish. Fresh and boneless.', 35),
            ]),
            # Coffee & Tea
            ('coffee-tea', [
                ('Arabica Coffee (500g)', 'arabica-coffee-500g', 35000, 'Premium Arabica coffee from Mt. Elgon. Medium roast.', 30),
                ('Robusta Coffee (1kg)', 'robusta-coffee-1kg', 28000, 'Strong Robusta coffee. Dark roast, full-bodied.', 40),
                ('Green Tea (250g)', 'green-tea-250g', 15000, 'Organic green tea from Toro. Health benefits.', 25),
            ]),
            # Honey & Bee Products
            ('honey-bee-products', [
                ('Pure Honey (1kg)', 'pure-honey-1kg', 40000, 'Raw unprocessed honey from Kidepo. 100% pure.', 25),
                ('Propolis Extract (100ml)', 'propolis-extract', 25000, 'Natural propolis for immunity boost.', 15),
            ]),
        ]
        
        created_count = 0
        for cat_slug, products in products_data:
            try:
                category = Category.objects.get(slug=cat_slug)
                for name, slug, price, description, stock in products:
                    product, created = Product.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'name': name,
                            'category': category,
                            'price': Decimal(str(price)),
                            'description': description,
                            'stock': stock,
                            'is_active': True,
                            'is_featured': stock > 50,  # Feature high-stock items
                        }
                    )
                    if created:
                        created_count += 1
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  Category {cat_slug} not found, skipping...'))
        
        self.stdout.write(f'  Created {created_count} products')
