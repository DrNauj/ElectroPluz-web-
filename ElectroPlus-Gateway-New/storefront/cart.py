from decimal import Decimal

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'name': product.name,
                'image': product.image,
                'id': product_id
            }
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        # Resolve thumbnails and totals on iteration to keep session small
        from .models import Product
        for product_id, item in self.cart.items():
            try:
                product = Product.objects.get(id=product_id)
            except Exception:
                product = None

            # Determine thumbnail: prefer ProductImage, then ProductMedia image, then stored item image
            thumbnail = item.get('image')
            if product:
                try:
                    img = product.images.first()
                    if img and getattr(img, 'image'):
                        thumbnail = img.image.url
                    else:
                        media_img = product.media.filter(media_type='image').first()
                        if media_img and getattr(media_img, 'media_file'):
                            thumbnail = media_img.media_file.url
                except Exception:
                    pass

            item['thumbnail'] = thumbnail
            item['total_price'] = Decimal(item['price']) * item['quantity']
            item['id'] = product_id
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session['cart']
        self.save()