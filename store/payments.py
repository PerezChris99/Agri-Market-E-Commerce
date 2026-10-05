"""
Mobile Money Payment Integration for Uganda
Supports: MTN Mobile Money, Airtel Money
Using: Africa's Talking API / Flutterwave / Direct Integration

This module provides a unified interface for mobile money payments in Uganda.
"""

import requests
import hashlib
import hmac
import base64
import json
import logging
from decimal import Decimal
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MobileMoneyError(Exception):
    """Custom exception for mobile money errors"""
    pass


class BaseMobileMoneyProvider:
    """Base class for mobile money providers"""
    
    def __init__(self):
        self.base_url = ""
        self.api_key = ""
        self.api_secret = ""
        self.environment = 'sandbox'
    
    def initiate_payment(self, phone_number, amount, reference, description=""):
        """Initiate a payment request"""
        raise NotImplementedError
    
    def check_status(self, transaction_id):
        """Check payment status"""
        raise NotImplementedError
    
    def format_phone(self, phone):
        """Format phone number to 256XXXXXXXXX format"""
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        
        # Remove leading + if present
        if phone.startswith('+'):
            phone = phone[1:]
        
        # Convert 07XX to 2567XX
        if phone.startswith('07') and len(phone) == 10:
            phone = '256' + phone[1:]
        elif phone.startswith('7') and len(phone) == 9:
            phone = '256' + phone
        
        return phone
    
    def validate_phone(self, phone, provider='any'):
        """Validate Uganda phone number"""
        phone = self.format_phone(phone)
        
        if len(phone) != 12 or not phone.startswith('256'):
            return False, "Invalid phone number format"
        
        # MTN prefixes: 77, 78, 76, 39
        mtn_prefixes = ['25677', '25678', '25676', '25639']
        # Airtel prefixes: 70, 75, 74
        airtel_prefixes = ['25670', '25675', '25674']
        
        if provider == 'mtn':
            if not any(phone.startswith(p) for p in mtn_prefixes):
                return False, "Please use an MTN number (077, 078, 076)"
        elif provider == 'airtel':
            if not any(phone.startswith(p) for p in airtel_prefixes):
                return False, "Please use an Airtel number (070, 075, 074)"
        else:
            all_prefixes = mtn_prefixes + airtel_prefixes
            if not any(phone.startswith(p) for p in all_prefixes):
                return False, "Invalid Ugandan mobile number"
        
        return True, phone


class MTNMobileMoneyProvider(BaseMobileMoneyProvider):
    """
    MTN Mobile Money Integration
    Uses MTN MoMo API (Collection API)
    Documentation: https://momodeveloper.mtn.com/
    """
    
    def __init__(self):
        super().__init__()
        self.environment = getattr(settings, 'MTN_MOMO_ENVIRONMENT', 'sandbox')
        self.subscription_key = getattr(settings, 'MTN_MOMO_SUBSCRIPTION_KEY', '')
        self.api_user = getattr(settings, 'MTN_MOMO_API_USER', '')
        self.api_key = getattr(settings, 'MTN_MOMO_API_KEY', '')
        self.callback_url = getattr(settings, 'MTN_MOMO_CALLBACK_URL', '')
        
        if self.environment == 'sandbox':
            self.base_url = "https://sandbox.momodeveloper.mtn.com"
        else:
            self.base_url = "https://proxy.momocentral.com"
    
    def get_access_token(self):
        """Get OAuth access token"""
        url = f"{self.base_url}/collection/token/"
        
        auth_string = f"{self.api_user}:{self.api_key}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        
        try:
            response = requests.post(url, headers=headers, timeout=(5, 15))
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"MTN token error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"MTN token exception: {str(e)}")
            return None
    
    def initiate_payment(self, phone_number, amount, reference, description="Payment for agricultural products"):
        """
        Initiate MTN MoMo collection request
        Returns: (success, transaction_id, message)
        """
        valid, result = self.validate_phone(phone_number, 'mtn')
        if not valid:
            return False, None, result
        
        phone_number = result
        access_token = self.get_access_token()
        
        if not access_token:
            return False, None, "Could not connect to MTN. Please try again."
        
        url = f"{self.base_url}/collection/v1_0/requesttopay"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Reference-Id': reference,
            'X-Target-Environment': self.environment,
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json',
            'X-Callback-Url': self.callback_url,
        }
        
        payload = {
            "amount": str(int(amount)),
            "currency": "UGX",
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": description[:160],
            "payeeNote": f"Agri-Market Order {reference}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=(5, 20))
            
            if response.status_code == 202:
                return True, reference, "Payment request sent. Please approve on your phone."
            else:
                error_msg = response.json().get('message', 'Payment request failed')
                logger.error(f"MTN payment error: {response.status_code} - {response.text}")
                return False, None, error_msg
                
        except requests.exceptions.Timeout:
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"MTN payment exception: {str(e)}")
            return False, None, "Payment service unavailable. Please try again."
    
    def check_status(self, reference):
        """
        Check MTN MoMo payment status
        Returns: (status, details)
        """
        access_token = self.get_access_token()
        if not access_token:
            return 'error', {'message': 'Could not connect to MTN'}
        
        url = f"{self.base_url}/collection/v1_0/requesttopay/{reference}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Target-Environment': self.environment,
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', '').upper()
                
                if status == 'SUCCESSFUL':
                    return 'successful', {
                        'transaction_id': data.get('financialTransactionId'),
                        'payer': data.get('payer', {}).get('partyId'),
                    }
                elif status == 'PENDING':
                    return 'pending', {'message': 'Waiting for user approval'}
                elif status == 'FAILED':
                    reason = data.get('reason', {}).get('message', 'Payment was declined')
                    return 'failed', {'message': reason}
                else:
                    return 'unknown', {'message': f'Unknown status: {status}'}
            else:
                return 'error', {'message': 'Could not check payment status'}
                
        except Exception as e:
            logger.error(f"MTN status check exception: {str(e)}")
            return 'error', {'message': 'Service unavailable'}


class AirtelMoneyProvider(BaseMobileMoneyProvider):
    """
    Airtel Money Integration
    Uses Airtel Money API
    Documentation: https://developers.airtel.africa/
    """
    
    def __init__(self):
        super().__init__()
        self.environment = getattr(settings, 'AIRTEL_ENVIRONMENT', 'sandbox')
        self.client_id = getattr(settings, 'AIRTEL_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'AIRTEL_CLIENT_SECRET', '')
        self.callback_url = getattr(settings, 'AIRTEL_CALLBACK_URL', '')
        
        if self.environment == 'sandbox':
            self.base_url = "https://openapiuat.airtel.africa"
        else:
            self.base_url = "https://openapi.airtel.africa"
    
    def get_access_token(self):
        """Get OAuth access token"""
        url = f"{self.base_url}/auth/oauth2/token"
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get('access_token')
            else:
                logger.error(f"Airtel token error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Airtel token exception: {str(e)}")
            return None
    
    def initiate_payment(self, phone_number, amount, reference, description="Payment for agricultural products"):
        """
        Initiate Airtel Money collection request
        Returns: (success, transaction_id, message)
        """
        valid, result = self.validate_phone(phone_number, 'airtel')
        if not valid:
            return False, None, result
        
        phone_number = result
        access_token = self.get_access_token()
        
        if not access_token:
            return False, None, "Could not connect to Airtel. Please try again."
        
        url = f"{self.base_url}/merchant/v1/payments/"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Country': 'UG',
            'X-Currency': 'UGX',
            'Content-Type': 'application/json',
        }
        
        payload = {
            "reference": reference,
            "subscriber": {
                "country": "UG",
                "currency": "UGX",
                "msisdn": phone_number[3:]  # Remove 256 prefix
            },
            "transaction": {
                "amount": int(amount),
                "country": "UG",
                "currency": "UGX",
                "id": reference
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            data = response.json()
            
            if response.status_code == 200 and data.get('status', {}).get('success'):
                return True, reference, "Payment request sent. Please approve on your phone."
            else:
                error_msg = data.get('status', {}).get('message', 'Payment request failed')
                logger.error(f"Airtel payment error: {response.text}")
                return False, None, error_msg
                
        except requests.exceptions.Timeout:
            return False, None, "Request timed out. Please try again."
        except Exception as e:
            logger.error(f"Airtel payment exception: {str(e)}")
            return False, None, "Payment service unavailable. Please try again."
    
    def check_status(self, reference):
        """
        Check Airtel Money payment status
        Returns: (status, details)
        """
        access_token = self.get_access_token()
        if not access_token:
            return 'error', {'message': 'Could not connect to Airtel'}
        
        url = f"{self.base_url}/standard/v1/payments/{reference}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Country': 'UG',
            'X-Currency': 'UGX',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                transaction = data.get('data', {}).get('transaction', {})
                status = transaction.get('status', '').upper()
                
                if status == 'TS':  # Transaction Successful
                    return 'successful', {
                        'transaction_id': transaction.get('id'),
                        'airtel_money_id': transaction.get('airtel_money_id'),
                    }
                elif status == 'TIP':  # Transaction In Progress
                    return 'pending', {'message': 'Waiting for user approval'}
                elif status in ['TF', 'TA']:  # Failed or Ambiguous
                    return 'failed', {'message': transaction.get('message', 'Payment was declined')}
                else:
                    return 'unknown', {'message': f'Unknown status: {status}'}
            else:
                return 'error', {'message': 'Could not check payment status'}
                
        except Exception as e:
            logger.error(f"Airtel status check exception: {str(e)}")
            return 'error', {'message': 'Service unavailable'}


class FlutterwaveProvider:
    """
    Flutterwave Payment Integration
    Supports both MTN and Airtel via a single API
    Documentation: https://developer.flutterwave.com/
    """
    
    def __init__(self):
        self.secret_key = getattr(settings, 'FLUTTERWAVE_SECRET_KEY', '')
        self.public_key = getattr(settings, 'FLUTTERWAVE_PUBLIC_KEY', '')
        self.encryption_key = getattr(settings, 'FLUTTERWAVE_ENCRYPTION_KEY', '')
        self.base_url = "https://api.flutterwave.com/v3"
    
    def initiate_payment(self, phone_number, amount, reference, email="", provider='mtn', description=""):
        """
        Initiate Flutterwave mobile money charge
        Returns: (success, transaction_id, message, data)
        """
        url = f"{self.base_url}/charges?type=mobile_money_uganda"
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }
        
        # Format phone number
        phone = str(phone_number).strip().replace(" ", "").replace("-", "")
        if phone.startswith('0'):
            phone = '256' + phone[1:]
        elif not phone.startswith('256'):
            phone = '256' + phone
        
        # Determine network
        network = 'MTN' if provider == 'mtn' else 'AIRTEL'
        
        payload = {
            "phone_number": phone,
            "amount": int(amount),
            "currency": "UGX",
            "email": email or "customer@agrimarket.ug",
            "tx_ref": reference,
            "network": network,
            "meta": {
                "source": "agri-market",
                "description": description or "Agricultural product purchase"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            data = response.json()
            
            if data.get('status') == 'success':
                return True, data.get('data', {}).get('id'), "Payment initiated. Please approve on your phone.", data
            else:
                error_msg = data.get('message', 'Payment request failed')
                logger.error(f"Flutterwave error: {response.text}")
                return False, None, error_msg, data
                
        except Exception as e:
            logger.error(f"Flutterwave exception: {str(e)}")
            return False, None, "Payment service unavailable", {}
    
    def verify_transaction(self, transaction_id):
        """
        Verify Flutterwave transaction
        Returns: (status, data)
        """
        url = f"{self.base_url}/transactions/{transaction_id}/verify"
        
        headers = {
            'Authorization': f'Bearer {self.secret_key}',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'success':
                tx_data = data.get('data', {})
                status = tx_data.get('status', '').lower()
                
                if status == 'successful':
                    return 'successful', {
                        'transaction_id': tx_data.get('id'),
                        'flw_ref': tx_data.get('flw_ref'),
                        'amount': tx_data.get('amount'),
                    }
                elif status == 'pending':
                    return 'pending', {'message': 'Transaction pending'}
                else:
                    return 'failed', {'message': tx_data.get('processor_response', 'Payment failed')}
            else:
                return 'error', {'message': data.get('message', 'Verification failed')}
                
        except Exception as e:
            logger.error(f"Flutterwave verify exception: {str(e)}")
            return 'error', {'message': 'Service unavailable'}


class PaymentGateway:
    """
    Unified payment gateway for all mobile money providers
    Usage:
        gateway = PaymentGateway()
        success, txn_id, message = gateway.initiate_payment(
            provider='mtn',
            phone='0771234567',
            amount=50000,
            reference='AGR-123',
            email='customer@email.com'
        )
    """
    
    PROVIDER_CLASSES = {
        'mtn': MTNMobileMoneyProvider,
        'airtel': AirtelMoneyProvider,
        'flutterwave': FlutterwaveProvider,
    }
    
    def __init__(self, use_flutterwave=True):
        """
        Initialize payment gateway.
        use_flutterwave: Use Flutterwave as unified provider (recommended for simplicity)
        """
        configured_provider = getattr(settings, 'MOBILE_MONEY_PROVIDER', 'flutterwave').lower()
        self.use_flutterwave = use_flutterwave and configured_provider == 'flutterwave'

        # Check if Flutterwave is configured
        if self.use_flutterwave and getattr(settings, 'FLUTTERWAVE_SECRET_KEY', ''):
            self.default_provider = FlutterwaveProvider()
        else:
            self.use_flutterwave = False
    
    def get_provider(self, provider_name):
        """Get specific provider instance"""
        if self.use_flutterwave:
            return self.default_provider

        provider_class = self.PROVIDER_CLASSES.get(provider_name)
        if not provider_class:
            raise MobileMoneyError(f"Unknown provider: {provider_name}")
        return provider_class()
    
    def detect_provider(self, phone_number):
        """Auto-detect provider from phone number"""
        phone = str(phone_number).strip().replace(" ", "").replace("-", "")
        
        # Convert to 256 format
        if phone.startswith('0'):
            phone = '256' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        
        # MTN prefixes
        if any(phone.startswith(p) for p in ['25677', '25678', '25676', '25639']):
            return 'mtn'
        # Airtel prefixes
        elif any(phone.startswith(p) for p in ['25670', '25675', '25674']):
            return 'airtel'
        else:
            return None
    
    def initiate_payment(self, provider, phone, amount, reference, email="", description=""):
        """
        Initiate mobile money payment
        
        Args:
            provider: 'mtn' or 'airtel'
            phone: Customer phone number
            amount: Amount in UGX
            reference: Unique transaction reference
            email: Customer email (for receipts)
            description: Payment description
        
        Returns:
            tuple: (success: bool, transaction_id: str, message: str)
        """
        try:
            # Auto-detect provider if not specified
            if not provider:
                provider = self.detect_provider(phone)
                if not provider:
                    return False, None, "Could not detect mobile network. Please select MTN or Airtel."
            
            if self.use_flutterwave:
                success, txn_id, message, _ = self.default_provider.initiate_payment(
                    phone_number=phone,
                    amount=amount,
                    reference=reference,
                    email=email,
                    provider=provider,
                    description=description
                )
                return success, txn_id, message
            else:
                provider_instance = self.get_provider(provider)
                return provider_instance.initiate_payment(
                    phone_number=phone,
                    amount=amount,
                    reference=reference,
                    description=description
                )
                
        except MobileMoneyError as e:
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Payment gateway error: {str(e)}")
            return False, None, "Payment service temporarily unavailable"
    
    def check_status(self, provider, reference):
        """
        Check payment status
        
        Returns:
            tuple: (status: str, details: dict)
            status: 'successful', 'pending', 'failed', 'error'
        """
        try:
            if self.use_flutterwave:
                return self.default_provider.verify_transaction(reference)
            else:
                provider_instance = self.get_provider(provider)
                return provider_instance.check_status(reference)
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            return 'error', {'message': 'Could not check payment status'}
    
    def format_amount(self, amount):
        """Format amount for display (UGX)"""
        return f"UGX {int(amount):,}"


def verify_paypal_transaction(order_id, expected_ugx_amount):
    """Verify a captured PayPal order server-side before completing Agri-Market checkout."""
    client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
    client_secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
    if not client_id or not client_secret or not order_id:
        return False

    mode = getattr(settings, 'PAYPAL_MODE', 'sandbox').lower()
    base_url = 'https://api-m.paypal.com' if mode == 'live' else 'https://api-m.sandbox.paypal.com'
    try:
        token_response = requests.post(
            f'{base_url}/v1/oauth2/token',
            auth=(client_id, client_secret),
            data={'grant_type': 'client_credentials'},
            headers={'Accept': 'application/json'},
            timeout=20,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')
        if not access_token:
            return False

        response = requests.get(
            f'{base_url}/v2/checkout/orders/{order_id}',
            headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get('status') != 'COMPLETED':
            return False

        expected_usd = (Decimal(str(expected_ugx_amount)) / Decimal(str(getattr(settings, 'USD_TO_UGX_RATE', 3700)))).quantize(Decimal('0.01'))
        purchase_units = payload.get('purchase_units') or []
        if not purchase_units:
            return False
        captured = purchase_units[0].get('payments', {}).get('captures', [])
        if not captured or captured[0].get('status') != 'COMPLETED':
            return False
        actual_usd = Decimal(str(captured[0].get('amount', {}).get('value', '0')))
        return actual_usd == expected_usd
    except (requests.RequestException, ValueError, ArithmeticError):
        logger.exception('PayPal server-side verification failed for order %s', order_id)
        return False


# Utility functions for quick access
def initiate_mobile_payment(phone, amount, reference, provider=None, email=""):
    """Quick function to initiate mobile money payment"""
    gateway = PaymentGateway()
    return gateway.initiate_payment(
        provider=provider,
        phone=phone,
        amount=amount,
        reference=reference,
        email=email
    )


def check_payment_status(reference, provider='mtn'):
    """Quick function to check payment status"""
    gateway = PaymentGateway()
    return gateway.check_status(provider, reference)
