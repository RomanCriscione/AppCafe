from django.urls import path
from .mobile_api import (
    CafeDetailAPIView,
    RelatedCafesAPIView,
    MeAPIView,
    MyMapAPIView,
    SetCafeStatusAPIView,
    SetCafeCollectionAPIView,
    CreateCafeAPIView,
    BecomeOwnerAPIView,
    CreateReviewAPIView,
    ReviewTagsAPIView,
    UpdateReviewAPIView,
    ReportReviewAPIView,
    CafeWhispersAPIView,
)

from .auth_api import (
    MobileLoginAPIView,
    MobileGoogleLoginAPIView,
    MobileAppleLoginAPIView,
    MobileRegisterAPIView,
    MobileLogoutAPIView,
    MobileDeleteAccountAPIView,
    MobileChangePasswordAPIView,
    MobilePasswordResetAPIView,
)


urlpatterns = [
    path(
        "my-map/",
        MyMapAPIView.as_view(),
        name="mobile-my-map",
    ),

    path(
        "me/",
        MeAPIView.as_view(),
        name="mobile-me",
    ),
    path(
        "become-owner/",
        BecomeOwnerAPIView.as_view(),
        name="mobile-become-owner",
    ),

    path(
        "login/",
        MobileLoginAPIView.as_view(),
        name="mobile-login",
    ),

    path(
        "google-login/",
        MobileGoogleLoginAPIView.as_view(),
        name="mobile-google-login",
    ),

    path(
        "apple-login/",
        MobileAppleLoginAPIView.as_view(),
        name="mobile-apple-login",
    ),

    path(
        "register/",
        MobileRegisterAPIView.as_view(),
        name="mobile-register",
    ),

    path(
        "password-reset/",
        MobilePasswordResetAPIView.as_view(),
        name="mobile-password-reset",
    ),

    path(
        "change-password/",
        MobileChangePasswordAPIView.as_view(),
        name="mobile-change-password",
    ),

    path(
        "logout/",
        MobileLogoutAPIView.as_view(),
        name="mobile-logout",
    ),

    path(
        "delete-account/",
        MobileDeleteAccountAPIView.as_view(),
        name="mobile-delete-account",
    ),

    path(
        "cafes/create/",
        CreateCafeAPIView.as_view(),
        name="mobile-create-cafe",
    ),

    path(
        "cafes/<int:cafe_id>/",
        CafeDetailAPIView.as_view(),
        name="mobile-cafe-detail",
    ),

    path(
        "cafes/<int:cafe_id>/reviews/create/",
        CreateReviewAPIView.as_view(),
        name="mobile-create-review",
    ),

    path(
        "reviews/<int:review_id>/",
        UpdateReviewAPIView.as_view(),
        name="mobile-update-review",
    ),

    path(
        "reviews/<int:review_id>/report/",
        ReportReviewAPIView.as_view(),
        name="mobile-report-review",
    ),

    path(
        "review-tags/",
        ReviewTagsAPIView.as_view(),
        name="mobile-review-tags",
    ),

    path(
        "cafes/<int:cafe_id>/whispers/",
        CafeWhispersAPIView.as_view(),
        name="mobile-cafe-whispers",
    ),

    path(
        "cafes/<int:cafe_id>/related/",
        RelatedCafesAPIView.as_view(),
        name="mobile-related-cafes",
    ),

    path(
        "cafes/<int:cafe_id>/set-status/",
        SetCafeStatusAPIView.as_view(),
        name="mobile-set-cafe-status",
    ),
    path(
        "cafes/<int:cafe_id>/set-collection/",
        SetCafeCollectionAPIView.as_view(),
        name="mobile-set-cafe-collection",
    ),
]