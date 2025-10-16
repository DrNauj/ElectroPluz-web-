@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating'))
        comment = request.POST.get('comment')
        
        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating,
                'comment': comment
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Reseña agregada exitosamente',
            'avg_rating': product.avg_rating,
            'review_count': product.review_count
        })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

def chatbot_response(request):
    """Vista para manejar las respuestas del chatbot de atención al cliente."""
    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip().lower()
        
        # Lógica simple del chatbot basada en reglas
        response = get_chatbot_response(user_message)
        
        return JsonResponse({
            'response': response,
            'timestamp': timezone.now().strftime('%H:%M')
        })
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def get_chatbot_response(message):
    """Función que genera respuestas del chatbot basadas en el mensaje del usuario."""
    
    # Palabras clave y respuestas
    responses = {
        # Saludos
        'hola': '¡Hola! Soy el asistente virtual de ElectroPlus. ¿En qué puedo ayudarte hoy?',
        'buenos dias': '¡Buenos días! ¿Cómo puedo ayudarte con tu compra en ElectroPlus?',
        'buenas tardes': '¡Buenas tardes! Estoy aquí para resolver tus dudas sobre nuestros productos.',
        'buenas noches': '¡Buenas noches! Aunque es tarde, estoy aquí para ayudarte.',
        
        # Información de productos
        'producto': 'Tenemos una amplia gama de productos electrónicos: computadoras, celulares, televisores, consolas y más. ¿Qué tipo de producto buscas?',
        'precio': 'Los precios de nuestros productos varían según el modelo y las ofertas disponibles. ¿Me puedes decir qué producto te interesa?',
        'stock': 'Para verificar la disponibilidad de stock, te recomiendo buscar el producto en nuestra tienda online o contactar a nuestro equipo de ventas.',
        
        # Pedidos y envíos
        'pedido': 'Para hacer un pedido, simplemente agrega los productos al carrito y procede al checkout. ¿Necesitas ayuda con algún pedido específico?',
        'envio': 'Realizamos envíos a todo el Perú. Los tiempos de entrega varían según la ubicación: Lima (1-2 días), provincias (3-5 días). El costo depende del peso y destino.',
        'entrega': 'El tiempo de entrega depende de tu ubicación. Para Lima: 1-2 días hábiles. Para provincias: 3-5 días hábiles. Te enviaremos actualizaciones por email.',
        
        # Devoluciones y cambios
        'devolucion': 'Aceptamos devoluciones dentro de 7 días después de la entrega, siempre que el producto esté en perfectas condiciones. Contacta a nuestro equipo para iniciar el proceso.',
        'cambio': 'Los cambios están sujetos a disponibilidad de stock. Puedes cambiar tu producto por otro de igual o mayor valor. El costo adicional se cobra por diferencia.',
        'garantia': 'Todos nuestros productos tienen garantía oficial del fabricante. La duración varía según el producto (6 meses a 2 años).',
        
        # Pagos
        'pago': 'Aceptamos tarjetas de crédito/débito, transferencias bancarias y pagos en efectivo contra entrega. Todos los pagos son seguros.',
        'tarjeta': 'Aceptamos Visa, Mastercard y American Express. Tu información de pago está protegida con encriptación SSL.',
        
        # Contacto
        'telefono': 'Puedes contactarnos al: 01-123-4567 (Lima) o al WhatsApp: +51 987 654 321.',
        'email': 'Nuestro email de atención al cliente es: soporte@electroplus.com.pe',
        'direccion': 'Nuestra tienda principal está en Av. Larco 123, Miraflores, Lima. También atendemos en nuestros locales de San Miguel y Surco.',
        
        # Ayuda general
        'ayuda': 'Estoy aquí para ayudarte con información sobre productos, pedidos, envíos, devoluciones y más. ¿Qué necesitas saber?',
        'gracias': '¡De nada! Fue un placer ayudarte. Si tienes más preguntas, no dudes en consultar.',
        'adios': '¡Hasta luego! Gracias por elegir ElectroPlus. ¡Que tengas un excelente día!',
        'chao': '¡Chao! Recuerda que estamos aquí para cualquier consulta futura.',
    }
    
    # Buscar coincidencias exactas primero
    if message in responses:
        return responses[message]
    
    # Buscar palabras clave en el mensaje
    for keyword, response in responses.items():
        if keyword in message:
            return response
    
    # Respuestas por defecto
    if any(word in message for word in ['como', 'donde', 'cuando', 'que', 'cual']):
        return 'Para obtener información más específica, te recomiendo contactar directamente con nuestro equipo de atención al cliente al 01-123-4567 o por email a soporte@electroplus.com.pe'
    
    if any(word in message for word in ['problema', 'error', 'no funciona', 'defecto']):
        return 'Lamento escuchar que tienes un problema. Por favor, contacta a nuestro equipo técnico al 01-123-4567 para recibir asistencia especializada.'
    
    # Respuesta por defecto
    return 'Disculpa, no entendí tu consulta. ¿Podrías reformularla? Estoy aquí para ayudarte con información sobre productos, pedidos, envíos y atención al cliente.'

def chatbot(request):
    """Vista principal del chatbot."""
    return render(request, 'storefront/chatbot.html')
