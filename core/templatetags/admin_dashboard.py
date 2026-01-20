from django import template
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model
from core.models import DisputeReport, RentalRequest, Review
import json

register = template.Library()
User = get_user_model()

@register.simple_tag
def get_dashboard_stats():
    # --- KPI Data ---
    total_users = User.objects.count()
    total_disputes = DisputeReport.objects.count()
    ongoing_rentals = RentalRequest.objects.filter(status="Ongoing").count()
    total_reviews = Review.objects.count()

    # --- Chart 1: User Registration Trend (Group by Month) ---
    # Note: Ensure your User model has 'date_joined' (Standard Django User has this)
    user_trend = User.objects.annotate(month=TruncMonth('date_joined')) \
                             .values('month') \
                             .annotate(count=Count('id')) \
                             .order_by('month')
    
    trend_labels = [entry['month'].strftime('%b %Y') for entry in user_trend] if user_trend else []
    trend_data = [entry['count'] for entry in user_trend] if user_trend else []

    # --- Chart 2: Rental Status Distribution ---
    rental_status = RentalRequest.objects.values('status').annotate(count=Count('id'))
    
    status_labels = [entry['status'] for entry in rental_status]
    status_data = [entry['count'] for entry in rental_status]

    return {
        'kpi': {
            'users': total_users,
            'disputes': total_disputes,
            'ongoing': ongoing_rentals,
            'reviews': total_reviews
        },
        'charts': {
            'trend_labels': json.dumps(trend_labels),
            'trend_data': json.dumps(trend_data),
            'status_labels': json.dumps(status_labels),
            'status_data': json.dumps(status_data),
        }
    }