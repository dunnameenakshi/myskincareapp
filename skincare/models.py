from django.db import models


SKIN_TYPE_CHOICES = [
    ('oily', 'Oily'),
    ('dry', 'Dry'),
    ('combination', 'Combination'),
    ('normal', 'Normal'),
    ('sensitive', 'Sensitive'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('non_binary', 'Non-Binary'),
    ('prefer_not', 'Prefer not to say'),
]

CLIMATE_CHOICES = [
    ('tropical', 'Tropical'),
    ('dry', 'Dry / Arid'),
    ('temperate', 'Temperate'),
    ('continental', 'Continental'),
    ('polar', 'Polar / Cold'),
]

STRESS_LEVEL_CHOICES = [
    ('low', 'Low'),
    ('moderate', 'Moderate'),
    ('high', 'High'),
    ('very_high', 'Very High'),
]

DIET_TYPE_CHOICES = [
    ('omnivore', 'Omnivore'),
    ('vegetarian', 'Vegetarian'),
    ('vegan', 'Vegan'),
    ('keto', 'Keto'),
    ('gluten_free', 'Gluten-Free'),
    ('dairy_free', 'Dairy-Free'),
]

EXERCISE_FREQ_CHOICES = [
    ('none', 'Sedentary (no exercise)'),
    ('light', '1–2 days/week'),
    ('moderate', '3–4 days/week'),
    ('active', '5+ days/week'),
]

CONCERN_CHOICES = [
    ('acne', 'Acne / Breakouts'),
    ('dryness', 'Dryness / Flakiness'),
    ('oiliness', 'Excess Oiliness'),
    ('pigmentation', 'Pigmentation / Dark Spots'),
    ('wrinkles', 'Wrinkles / Fine Lines'),
    ('sensitivity', 'Sensitivity / Redness'),
    ('dark_circles', 'Dark Circles'),
    ('dullness', 'Dullness / Uneven Tone'),
    ('pores', 'Enlarged Pores'),
    ('sagging', 'Loss of Firmness / Sagging'),
]

TRIGGER_CHOICES = [
    ('stress', 'Stress'),
    ('diet', 'Diet / Food'),
    ('hormones', 'Hormonal Changes'),
    ('pollution', 'Pollution / Environment'),
    ('sun', 'Sun Exposure'),
    ('lack_sleep', 'Lack of Sleep'),
    ('products', 'Skincare Products'),
    ('unknown', 'Unknown'),
]


class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES)
    location = models.CharField(max_length=100, blank=True)
    climate_zone = models.CharField(max_length=20, choices=CLIMATE_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.skin_type} skin)"

    class Meta:
        db_table = 'user_profiles'


class SkinConcernAssessment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='assessments')
    primary_concerns = models.CharField(
        max_length=500,
        help_text="Comma-separated concern keys e.g. acne,dryness,pigmentation"
    )
    concern_duration_weeks = models.PositiveIntegerField(
        default=4,
        help_text="How long the concern has persisted (in weeks)"
    )
    known_triggers = models.CharField(
        max_length=300,
        blank=True,
        help_text="Comma-separated trigger keys e.g. stress,diet"
    )
    uses_cleanser = models.BooleanField(default=False)
    uses_moisturizer = models.BooleanField(default=False)
    uses_spf = models.BooleanField(default=False)
    uses_serum = models.BooleanField(default=False)
    uses_exfoliant = models.BooleanField(default=False)
    current_products_notes = models.TextField(
        blank=True,
        help_text="Free text: any products currently in use"
    )
    sleep_hours_per_night = models.FloatField(
        default=7.0,
        help_text="Average hours of sleep per night"
    )
    water_intake_liters = models.FloatField(
        default=2.0,
        help_text="Average daily water intake in liters"
    )
    diet_type = models.CharField(max_length=20, choices=DIET_TYPE_CHOICES, default='omnivore')
    stress_level = models.CharField(max_length=20, choices=STRESS_LEVEL_CHOICES, default='moderate')
    exercise_frequency = models.CharField(max_length=20, choices=EXERCISE_FREQ_CHOICES, default='light')
    smokes = models.BooleanField(default=False)
    alcohol_consumption = models.BooleanField(default=False)
    # skin_photo = models.ImageField(upload_to='skin_photos/', null=True, blank=True)
    known_allergies = models.TextField(blank=True, help_text="Any known ingredient allergies")

    created_at = models.DateTimeField(auto_now_add=True)

    def get_concerns_list(self):
        return [c.strip() for c in self.primary_concerns.split(',') if c.strip()]

    def get_triggers_list(self):
        return [t.strip() for t in self.known_triggers.split(',') if t.strip()]

    def __str__(self):
        return f"Assessment for {self.user.name} on {self.created_at.date()}"

    class Meta:
        db_table = 'skin_assessments'


class LifestyleRecommendation(models.Model):
    assessment = models.OneToOneField(
        SkinConcernAssessment, on_delete=models.CASCADE, related_name='recommendation'
    )
    diet_advice = models.TextField(help_text="Foods to include and avoid")
    foods_to_include = models.TextField(blank=True)
    foods_to_avoid = models.TextField(blank=True)
    # hydration_tips = models.TextField(blank=True)
    # sleep_tips = models.TextField(blank=True)
    # stress_management = models.TextField(blank=True)
    # exercise_suggestions = models.TextField(blank=True)
    # morning_routine = models.TextField(help_text="Step-by-step morning skincare routine")
    # night_routine = models.TextField(help_text="Step-by-step night skincare routine")
    # weekly_treatments = models.TextField(blank=True, help_text="Masks, exfoliation schedule etc.")
    # ingredients_to_seek = models.TextField(blank=True, help_text="Beneficial ingredients for the concern")
    # ingredients_to_avoid = models.TextField(blank=True, help_text="Ingredients to steer clear of")
    # budget_products = models.TextField(blank=True)
    # mid_range_products = models.TextField(blank=True)
    # premium_products = models.TextField(blank=True)
    # general_tips = models.TextField(blank=True)
    ai_model_used = models.CharField(max_length=100, default='gemini-2.5-flash')
    generated_at = models.DateTimeField(auto_now_add=True)
    confidence_score = models.FloatField(null=True, blank=True, help_text="0.0 to 1.0")

    def __str__(self):
        return f"Recommendation for {self.assessment.user.name} ({self.generated_at.date()})"

    class Meta:
        db_table = 'lifestyle_recommendations'
