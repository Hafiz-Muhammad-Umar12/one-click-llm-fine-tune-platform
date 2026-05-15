import uuid
import logging
import stripe
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.core.config import settings
from src.models.billing import UsageRecord, StripeCustomer
from src.models.models import Organization

logger = logging.getLogger(__name__)

if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

class UsageService:
    """
    Handles recording and aggregating usage data for billing.
    """
    async def record_usage(
        self, 
        db: AsyncSession, 
        organization_id: uuid.UUID, 
        resource_type: str, 
        quantity: float, 
        unit: str,
        resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        record = UsageRecord(
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            quantity=quantity,
            unit=unit,
            metadata_payload=metadata or {}
        )
        db.add(record)
        await db.commit()
        return record

    async def get_total_usage(
        self, db: AsyncSession, organization_id: uuid.UUID, resource_type: str
    ) -> float:
        query = select(func.sum(UsageRecord.quantity)).where(
            UsageRecord.organization_id == organization_id,
            UsageRecord.resource_type == resource_type
        )
        result = await db.execute(query)
        return result.scalar() or 0.0

class BillingService:
    """
    Handles Stripe integration and subscription management.
    """
    async def create_customer(self, db: AsyncSession, organization: Organization) -> StripeCustomer:
        if not settings.STRIPE_API_KEY:
            logger.warning("Stripe API key not set, skipping customer creation.")
            return None

        # Create Stripe Customer
        stripe_cust = stripe.Customer.create(
            name=organization.name,
            metadata={"organization_id": str(organization.id)}
        )
        
        db_obj = StripeCustomer(
            organization_id=organization.id,
            stripe_customer_id=stripe_cust.id,
            plan_tier="free",
            subscription_status="inactive"
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_checkout_session(
        self, db: AsyncSession, organization_id: uuid.UUID, price_id: str
    ) -> str:
        query = select(StripeCustomer).where(StripeCustomer.organization_id == organization_id)
        result = await db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            raise ValueError("Stripe customer not found for organization")

        session = stripe.checkout.Session.create(
            customer=customer.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.BACKEND_CORS_ORIGINS[0]}/dashboard/settings/billing?success=true",
            cancel_url=f"{settings.BACKEND_CORS_ORIGINS[0]}/dashboard/settings/billing?canceled=true",
        )
        return session.url

    async def handle_webhook(self, db: AsyncSession, payload: str, sig_header: str):
        event = None
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

        if event['type'] == 'customer.subscription.created' or event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            customer_id = subscription['customer']
            status = subscription['status']
            
            query = select(StripeCustomer).where(StripeCustomer.stripe_customer_id == customer_id)
            result = await db.execute(query)
            db_customer = result.scalar_one_or_none()
            
            if db_customer:
                db_customer.stripe_subscription_id = subscription['id']
                db_customer.subscription_status = status
                # Map price ID to plan tier here
                db.add(db_customer)
                await db.commit()

usage_service = UsageService()
billing_service = BillingService()
