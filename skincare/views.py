import json
import logging
from google import genai
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, SkinConcernAssessment, LifestyleRecommendation
from skincare.agent.RAG.knowledge_base import search_knowledge_base
logger = logging.getLogger('skincare')

def build_prompt(assessment: SkinConcernAssessment) -> str:
    user = assessment.user
    concerns = ", ".join(assessment.get_concerns_list())
    triggers = ", ".join(assessment.get_triggers_list()) or "none identified"

    relevant_knowledge = search_knowledge_base(concerns,top_k=3)
    
    return f"""
            You are a dermatology and wellness expert. Based on the following user profile and skin concerns,
            provide detailed lifestyle recommendations in JSON format.

            USER PROFILE:
            - Name: {user.name}
            - Age: {user.age}
            - Gender: {user.gender}
            - Skin Type: {user.skin_type}
            - Climate Zone: {user.climate_zone}
            - Location: {user.location}

            SKIN CONCERNS:
            - Primary Concerns: {concerns}
            - Duration: {assessment.concern_duration_weeks} weeks
            - Known Triggers: {triggers}
            - Known Allergies: {assessment.known_allergies or 'none'}

            CURRENT ROUTINE:
            - Cleanser: {assessment.uses_cleanser}
            - Moisturizer: {assessment.uses_moisturizer}
            - SPF: {assessment.uses_spf}
            - Serum: {assessment.uses_serum}
            - Exfoliant: {assessment.uses_exfoliant}
            - Notes: {assessment.current_products_notes or 'none'}

            LIFESTYLE:
            - Sleep: {assessment.sleep_hours_per_night} hrs/night
            - Water Intake: {assessment.water_intake_liters} liters/day
            - Diet: {assessment.diet_type}
            - Stress Level: {assessment.stress_level}
            - Exercise: {assessment.exercise_frequency}
            - Smokes: {assessment.smokes}
            - Alcohol: {assessment.alcohol_consumption}

            RELEVANT_MEDICAL_KNOWLEDGE:
            {relevant_knowledge}
            
            Return a JSON object with these exact keys:
            {{
            "diet_advice": "...",
            "foods_to_include": "...",
            "foods_to_avoid": "...",
            "hydration_tips": "...",
            "sleep_tips": "...",
            "stress_management": "...",
            "exercise_suggestions": "...",
            "morning_routine": "...",
            "night_routine": "...",
            "weekly_treatments": "...",
            "ingredients_to_seek": "...",
            "ingredients_to_avoid": "...",
            "budget_products": "...",
            "mid_range_products": "...",
            "premium_products": "...",
            "general_tips": "...",
            "confidence_score": 0.0
            }}
            """


@csrf_exempt
def create_assessment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error parsing the json body'}, status=400)
    user, created = UserProfile.objects.get_or_create(
        name=data['name'],
        defaults={
            'age': data['age'],
            'gender': data['gender'],
            'skin_type': data['skin_type'],
            'location': data.get('location', ''),
            'climate_zone': data.get('climate_zone', ''),
        }
    )
    logger.info(f"User {data['name']} is created in database.")
    logger.info(f"CREATED ? {created}")
    

    assessment = SkinConcernAssessment.objects.create(
        user=user,
        primary_concerns=data['primary_concerns'],
        concern_duration_weeks=data.get('concern_duration_weeks', 4),
        known_triggers=data.get('known_triggers', ''),
        uses_cleanser=data.get('uses_cleanser', False),
        uses_moisturizer=data.get('uses_moisturizer', False),
        uses_spf=data.get('uses_spf', False),
        uses_serum=data.get('uses_serum', False),
        uses_exfoliant=data.get('uses_exfoliant', False),
        current_products_notes=data.get('current_products_notes', ''),
        sleep_hours_per_night=data.get('sleep_hours_per_night', 7.0),
        water_intake_liters=data.get('water_intake_liters', 2.0),
        diet_type=data.get('diet_type', 'omnivore'),
        stress_level=data.get('stress_level', 'moderate'),
        exercise_frequency=data.get('exercise_frequency', 'light'),
        smokes=data.get('smokes', False),
        alcohol_consumption=data.get('alcohol_consumption', False),
        known_allergies=data.get('known_allergies', ''),
    )
    logger.info(f"User {data['name']} assessment is created in database.")

    return generate_recommendation(request, assessment.id)


def generate_recommendation(request, assessment_id):
    try:
        assessment = SkinConcernAssessment.objects.get(id=assessment_id)
    except SkinConcernAssessment.DoesNotExist:
        return JsonResponse({'error': 'Assessment not found'}, status=404)
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)   # new way
        prompt = build_prompt(assessment)
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt
        )   
        # Strip markdown code fences if Gemini wraps the JSON
        raw = response.text.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
        result = json.loads(raw)
    except Exception as e:
        return JsonResponse({'error':f"Gemini server error - {e}"},status = 503)

    recommendation = LifestyleRecommendation.objects.create(
        assessment=assessment,
        diet_advice=result.get('diet_advice', ''),
        foods_to_include=result.get('foods_to_include', ''),
        foods_to_avoid=result.get('foods_to_avoid', ''),
        # hydration_tips=result.get('hydration_tips', ''),
        # sleep_tips=result.get('sleep_tips', ''),
        # stress_management=result.get('stress_management', ''),
        # exercise_suggestions=result.get('exercise_suggestions', ''),
        # morning_routine=result.get('morning_routine', ''),
        # night_routine=result.get('night_routine', ''),
        # weekly_treatments=result.get('weekly_treatments', ''),
        # ingredients_to_seek=result.get('ingredients_to_seek', ''),
        # ingredients_to_avoid=result.get('ingredients_to_avoid', ''),
        # budget_products=result.get('budget_products', ''),
        # mid_range_products=result.get('mid_range_products', ''),
        # premium_products=result.get('premium_products', ''),
        # general_tips=result.get('general_tips', ''),
        ai_model_used='gemini-3.8-flash',
        confidence_score=result.get('confidence_score', None),
    )
    logger.info(f"User {assessment.name} recommendation is created in database.")

    return JsonResponse({
        'assessment_id': assessment.id,
        'recommendation': {
            'diet_advice': recommendation.diet_advice,
            'foods_to_include': recommendation.foods_to_include,
            'foods_to_avoid': recommendation.foods_to_avoid,
            # 'morning_routine': recommendation.morning_routine,
            # 'night_routine': recommendation.night_routine,
            # 'ingredients_to_seek': recommendation.ingredients_to_seek,
            # 'ingredients_to_avoid': recommendation.ingredients_to_avoid,
            # 'general_tips': recommendation.general_tips,
            'generated_at': recommendation.generated_at.isoformat(),
        }
    })
