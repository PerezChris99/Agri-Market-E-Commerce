"""
SMS Notification Service for Uganda
Supports: Africa's Talking, Twilio, Local SMS Gateways

Sends order confirmations, payment receipts, delivery updates, and promotional messages.
"""

import requests
import logging
from django.conf import settings
from django.utils import timezone
from django.template import Template, Context

logger = logging.getLogger(__name__)


class SMSError(Exception):
    """Custom exception for SMS errors"""
    pass


# ============================================
# SMS MESSAGE TEMPLATES
# ============================================

SMS_TEMPLATES = {
    'order_confirmation': {
        'en': "Agri-Market: Your order #{{order_id}} has been received! Total: UGX {{total}}. We'll notify you when it's ready for delivery. Questions? Call us.",
        'lg': "Agri-Market: Order yo #{{order_id}} tufunye! Omuwendo: UGX {{total}}. Tujja kukumanyisa nga tekutandikira kutwaala. Ebibuuzo? Tukubire.",
    },
    'payment_received': {
        'en': "Agri-Market: Payment of UGX {{amount}} received for order #{{order_id}}. Thank you for shopping with us! Track: {{tracking_url}}",
        'lg': "Agri-Market: Tufunye ssente UGX {{amount}} ku order #{{order_id}}. Webale okutunda naffe! Goberera: {{tracking_url}}",
    },
    'order_shipped': {
        'en': "Agri-Market: Great news! Your order #{{order_id}} is on the way. Expected delivery: {{delivery_date}}. Rider: {{rider_name}} ({{rider_phone}})",
        'lg': "Agri-Market: Amawulire amalungi! Order yo #{{order_id}} etandise okujja. Tunasembeza: {{delivery_date}}. Rider: {{rider_name}} ({{rider_phone}})",
    },
    'order_delivered': {
        'en': "Agri-Market: Your order #{{order_id}} has been delivered! Thank you for choosing Agri-Market. Rate your experience: {{rating_url}}",
        'lg': "Agri-Market: Order yo #{{order_id}} evudde! Webale okulonda Agri-Market. Tuwe amagezi: {{rating_url}}",
    },
    'otp': {
        'en': "Agri-Market: Your verification code is {{otp}}. Valid for 10 minutes. Do not share this code with anyone.",
        'lg': "Agri-Market: Code yo ya kuzuula: {{otp}}. Ekola ddakiika 10. Togabana code eno na muntu yenna.",
    },
    'promotional': {
        'en': "Agri-Market: {{message}} Shop now at agrimarket.ug. Reply STOP to unsubscribe.",
        'lg': "Agri-Market: {{message}} Gula kati ku agrimarket.ug. Ddamu STOP okulekeraawo.",
    },
    'payment_reminder': {
        'en': "Agri-Market: Reminder - Your order #{{order_id}} (UGX {{total}}) is awaiting payment. Complete payment to process your order.",
        'lg': "Agri-Market: Kijjukizo - Order yo #{{order_id}} (UGX {{total}}) eyeeteera okusasulwa. Mala okusasula tusobole okukola order yo.",
    },
    'bulk_order_quote': {
        'en': "Agri-Market: Quote ready for your bulk order of {{quantity}}x {{product}}. Total: UGX {{total}}. Valid until {{expiry}}. Reply YES to accept.",
        'lg': "Agri-Market: Quotation ya bulk order yo {{quantity}}x {{product}} ewedde. Omuwendo: UGX {{total}}. Ekola okutuuka {{expiry}}. Ddamu YES okukkiriza.",
    },
}


class BaseSMSProvider:
    """Base class for SMS providers"""
    
    def send_sms(self, recipient, message):
        """
        Send SMS to recipient
        Returns: (success, message_id, cost)
        """
        raise NotImplementedError
    
    def format_phone(self, phone):
        """Format phone to international format"""
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        
        if phone.startswith('+'):
            phone = phone[1:]
        
        if phone.startswith('0') and len(phone) == 10:
            phone = '256' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '256' + phone
        
        return '+' + phone


class AfricasTalkingProvider(BaseSMSProvider):
    """
    Africa's Talking SMS Provider
    Popular in East Africa, supports UG, KE, TZ, etc.
    Documentation: https://africastalking.com/docs/sms
    """
    
    def __init__(self):
        self.username = getattr(settings, 'AT_USERNAME', '')
        self.api_key = getattr(settings, 'AT_API_KEY', '')
        self.sender_id = getattr(settings, 'AT_SENDER_ID', 'AgriMarket')
        self.base_url = "https://api.africastalking.com/version1/messaging"
    
    def send_sms(self, recipient, message):
        """Send SMS via Africa's Talking"""
        phone = self.format_phone(recipient)
        
        headers = {
            'apiKey': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        
        data = {
            'username': self.username,
            'to': phone,
            'message': message,
            'from': self.sender_id,
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, data=data, timeout=30)
            result = response.json()
            
            if response.status_code == 201:
                recipients = result.get('SMSMessageData', {}).get('Recipients', [])
                if recipients:
                    recipient_data = recipients[0]
                    status = recipient_data.get('status')
                    
                    if status == 'Success':
                        return True, recipient_data.get('messageId'), recipient_data.get('cost')
                    else:
                        return False, None, recipient_data.get('status')
            
            logger.error(f"AT SMS error: {response.text}")
            return False, None, "Failed to send SMS"
            
        except Exception as e:
            logger.error(f"AT SMS exception: {str(e)}")
            return False, None, str(e)


class TwilioProvider(BaseSMSProvider):
    """
    Twilio SMS Provider
    Global coverage, reliable
    Documentation: https://www.twilio.com/docs/sms
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    def send_sms(self, recipient, message):
        """Send SMS via Twilio"""
        phone = self.format_phone(recipient)
        
        try:
            response = requests.post(
                self.base_url,
                auth=(self.account_sid, self.auth_token),
                data={
                    'From': self.phone_number,
                    'To': phone,
                    'Body': message,
                },
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return True, data.get('sid'), None
            else:
                logger.error(f"Twilio SMS error: {response.text}")
                return False, None, "Failed to send SMS"
                
        except Exception as e:
            logger.error(f"Twilio SMS exception: {str(e)}")
            return False, None, str(e)


class SMSService:
    """
    Main SMS Service
    Handles template rendering and sending
    """
    
    def __init__(self, provider='africastalking'):
        """Initialize SMS service with specified provider"""
        providers = {
            'africastalking': AfricasTalkingProvider,
            'twilio': TwilioProvider,
        }
        
        # Check configured provider
        configured_provider = getattr(settings, 'SMS_PROVIDER', 'africastalking')
        provider_class = providers.get(configured_provider)
        
        if provider_class:
            self.provider = provider_class()
        else:
            self.provider = None
            logger.warning("No SMS provider configured")
    
    def render_template(self, template_name, language='en', context=None):
        """Render SMS template with context"""
        if context is None:
            context = {}
        
        templates = SMS_TEMPLATES.get(template_name, {})
        template_str = templates.get(language, templates.get('en', ''))
        
        if not template_str:
            raise SMSError(f"Template not found: {template_name}")
        
        # Use Django template engine for variables
        template = Template(template_str)
        ctx = Context(context)
        return template.render(ctx)
    
    def send(self, recipient, message, notification_type='promotional', order=None, customer=None):
        """
        Send SMS and log to database
        
        Args:
            recipient: Phone number
            message: Message text
            notification_type: Type for logging
            order: Related order (optional)
            customer: Related customer (optional)
        
        Returns:
            (success, message_id)
        """
        from .models import SMSNotification
        
        # Create notification record
        notification = SMSNotification(
            recipient=recipient,
            message=message[:480],  # Max 3 SMS
            notification_type=notification_type,
            order=order,
            customer=customer,
            status='pending'
        )
        notification.save()
        
        if not self.provider:
            notification.status = 'failed'
            notification.gateway_response = 'No SMS provider configured'
            notification.save()
            return False, None
        
        try:
            success, message_id, cost = self.provider.send_sms(recipient, message)
            
            if success:
                notification.status = 'sent'
                notification.gateway_message_id = message_id
                notification.sent_at = timezone.now()
                if cost:
                    try:
                        notification.cost = float(cost.replace('UGX ', '').replace('KES ', ''))
                    except:
                        pass
            else:
                notification.status = 'failed'
                notification.gateway_response = str(cost)
            
            notification.save()
            return success, message_id
            
        except Exception as e:
            notification.status = 'failed'
            notification.gateway_response = str(e)
            notification.save()
            logger.error(f"SMS send error: {str(e)}")
            return False, None
    
    def send_order_confirmation(self, order, language='en'):
        """Send order confirmation SMS"""
        customer = order.customer
        if not customer or not customer.phone:
            return False, "No phone number"
        
        if not customer.receive_sms:
            return False, "Customer opted out of SMS"
        
        message = self.render_template('order_confirmation', language, {
            'order_id': order.order_id,
            'total': f"{order.get_cart_total:,.0f}",
        })
        
        return self.send(
            recipient=customer.phone,
            message=message,
            notification_type='order_confirmation',
            order=order,
            customer=customer
        )
    
    def send_payment_received(self, order, amount, language='en'):
        """Send payment confirmation SMS"""
        customer = order.customer
        if not customer or not customer.phone or not customer.receive_sms:
            return False, "Cannot send"
        
        tracking_url = f"agrimarket.ug/track/{order.order_id}"
        
        message = self.render_template('payment_received', language, {
            'order_id': order.order_id,
            'amount': f"{amount:,.0f}",
            'tracking_url': tracking_url,
        })
        
        return self.send(
            recipient=customer.phone,
            message=message,
            notification_type='payment_received',
            order=order,
            customer=customer
        )
    
    def send_order_shipped(self, order, rider_name="", rider_phone="", delivery_date="", language='en'):
        """Send order shipped notification"""
        customer = order.customer
        if not customer or not customer.phone or not customer.receive_sms:
            return False, "Cannot send"
        
        message = self.render_template('order_shipped', language, {
            'order_id': order.order_id,
            'delivery_date': delivery_date or "Today",
            'rider_name': rider_name or "Our Rider",
            'rider_phone': rider_phone or "",
        })
        
        return self.send(
            recipient=customer.phone,
            message=message,
            notification_type='order_shipped',
            order=order,
            customer=customer
        )
    
    def send_otp(self, phone, otp, language='en'):
        """Send OTP verification code"""
        message = self.render_template('otp', language, {
            'otp': otp,
        })
        
        return self.send(
            recipient=phone,
            message=message,
            notification_type='otp'
        )


# Utility functions
def send_sms(phone, message, notification_type='promotional'):
    """Quick function to send SMS"""
    service = SMSService()
    return service.send(phone, message, notification_type)


def send_order_sms(order, notification_type='order_confirmation'):
    """Send order-related SMS"""
    service = SMSService()
    
    if notification_type == 'order_confirmation':
        return service.send_order_confirmation(order)
    elif notification_type == 'payment_received':
        return service.send_payment_received(order, order.get_cart_total)
    elif notification_type == 'order_shipped':
        return service.send_order_shipped(order)
    else:
        return False, "Unknown notification type"
