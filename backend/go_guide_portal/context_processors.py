from go_guide_portal.models import BusinessUnitUser
from go_guide_portal.navigation import get_nav_items, get_ui_texts


def _get_unit_for_user(user):
    if not user or not user.is_authenticated:
        return None
    try:
        link = BusinessUnitUser.objects.select_related("business_unit").get(user=user)
        return link.business_unit
    except BusinessUnitUser.DoesNotExist:
        return None


def portal_context(request):
    """
    Adds current business unit, navigation items, and UI texts to every template.
    """
    unit = _get_unit_for_user(getattr(request, "user", None))
    ui_texts = get_ui_texts(unit)
    return {
        "current_unit": unit,
        "nav_items": get_nav_items(unit),
        "ui_texts": ui_texts,
    }

