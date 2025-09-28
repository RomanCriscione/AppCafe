# reviews/utils/ownership.py
from typing import Iterable
from django.db import transaction
from django.utils import timezone
from reviews.claims import ClaimStatus


def assign_owner(cafe, user):
    """
    Asigna el usuario como dueño/manager del café sin romper tu modelo.
    Si tu Cafe tiene 'owner' o 'owners' lo respeta; si no, usa 'claimed_by'.
    """
    with transaction.atomic():
        updated_fields = []

        if hasattr(cafe, "owner_id"):         # FK único
            cafe.owner = user
            updated_fields.append("owner")
        elif hasattr(cafe, "owners"):         # M2M
            cafe.save()  # asegurar PK
            cafe.owners.add(user)
        else:
            cafe.claimed_by = user            # fallback
            updated_fields.append("claimed_by")

        cafe.claim_status = ClaimStatus.VERIFIED
        updated_fields.append("claim_status")
        cafe.save(update_fields=updated_fields)
