import logging
import json
from config import settings

logger = logging.getLogger("volunteer_copilot.gemini")

# Initialize Gemini if key is provided
api_key_configured = False
_genai_client = None

if settings.gemini_api_key:
    try:
        from google import genai
        from google.genai.errors import ClientError
        _genai_client = genai.Client(api_key=settings.gemini_api_key)
        api_key_configured = True
        logger.info("Google Gemini API (google-genai SDK) successfully configured.")
    except Exception as e:
        logger.error(f"Failed to configure Google Gemini API: {str(e)}")

MODEL_IDS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]

class GeminiService:

    @staticmethod
    def _get_mock_crowd_response(zones: list, threshold: float) -> dict:
        alerts = []
        instructions = "All gates are operating within normal limits. Monitor flow."

        overloaded = [z for z in zones if z.get("occupancy_rate", 0) >= threshold]
        if overloaded:
            alerts = [f"{z['zone_id']} is at critical capacity ({z['occupancy_rate']}%)." for z in overloaded]

            # Find a lower occupancy gate to redirect to
            underloaded = [z for z in zones if z.get("occupancy_rate", 0) < 60]
            recommend_gate = underloaded[0]["zone_id"] if underloaded else "Gate A"

            instructions = (
                f"ALERT: Bottleneck detected at {', '.join(z['zone_id'] for z in overloaded)}. "
                f"Action Required: Immediately redirect incoming fans from these overloaded areas to {recommend_gate}. "
                f"Volunteers should stand at key transit corridor intersections with megaphones directing traffic."
            )

        return {
            "alerts": alerts,
            "instructions": instructions,
            "is_mock": True
        }

    @staticmethod
    def _get_mock_translation_response(text: str, fan_lang: str, fan_origin: str, urgency: str, stress: str) -> dict:
        # Simple local mock response
        detected = "Spanish" if "bano" in text.lower() or "baño" in text.lower() else "Unknown"
        english_translation = f"Mock Translation of: '{text}'"

        if "bano" in text.lower() or "baño" in text.lower() or "restroom" in text.lower() or "toilet" in text.lower():
            english_translation = "Where is the restroom / bathroom?"

        is_medical = urgency in ["urgent", "emergency"] or stress == "panicked"

        if is_medical:
            volunteer_response_en = "Please calm down. I am calling medical assistance right now. Please sit down here, help is on the way."
            fan_response_translated = "Por favor, cálmese. Estoy llamando a asistencia médica ahora mismo. Por favor siéntese aquí, la ayuda está en camino."
        else:
            volunteer_response_en = "The nearest restroom is located behind Gate C, just past the merchandise store."
            fan_response_translated = "El baño más cercano está detrás de la Puerta C, justo al pasar la tienda de mercancías."

        return {
            "detected_language": detected,
            "fan_text_en": english_translation,
            "urgency_analysis": f"Urgency: {urgency.upper()}, Stress: {stress.upper()}. " + ("Medical emergency detected!" if is_medical else "Standard informational request."),
            "suggested_response_en": volunteer_response_en,
            "suggested_response_fan_lang": fan_response_translated,
            "is_mock": True
        }

    @staticmethod
    def _get_mock_script_response(scenario: str, target_gates: list, languages: list) -> dict:
        scripts = {}
        for lang in languages:
            l_lower = lang.lower()
            if "spanish" in l_lower:
                scripts["Spanish"] = (
                    "¡ATENCIÓN! Por favor, diríjase a la " + ", ".join(target_gates) + ". "
                    "El acceso por otras zonas está temporalmente restringido. ¡Gracias por su cooperación!"
                )
            elif "french" in l_lower:
                scripts["French"] = (
                    "ATTENTION S'IL VOUS PLAÎT! Veuillez vous diriger vers la " + ", ".join(target_gates) + ". "
                    "L'accès par les autres zones est temporairement limité. Merci pour votre coopération!"
                )
            else:
                scripts[lang] = f"[Mock translation of scenario to {lang} directing to {', '.join(target_gates)}]"

        return {
            "scenario": scenario,
            "broadcast_scripts": scripts,
            "is_mock": True
        }

    @classmethod
    def _generate_json_content(cls, prompt: str) -> str:
        last_exception = None
        for model in MODEL_IDS:
            try:
                response = _genai_client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"}
                )
                logger.info(f"Gemini model {model} generated content successfully.")
                return response.text
            except Exception as e:
                last_exception = e
                logger.warning(f"Gemini model {model} failed: {str(e)}")
                continue
        logger.error("All Gemini models failed to generate content.")
        raise last_exception or RuntimeError("Gemini content generation failed.")

    @classmethod
    def analyze_crowd(cls, zones: list, threshold: float) -> dict:
        if not api_key_configured or _genai_client is None:
            logger.warning("Gemini API key not configured. Using Mock Crowd Engine.")
            return cls._get_mock_crowd_response(zones, threshold)

        try:
            prompt = (
                f"You are the Operations AI Coordinator for FIFA World Cup 2026 stadium management.\n"
                f"Analyze this live stadium crowd capacity data:\n"
                f"{json.dumps(zones, indent=2)}\n\n"
                f"Alert threshold is {threshold}% occupancy.\n\n"
                f"Perform the following tasks:\n"
                f"1. Identify which zones (if any) are at or above the threshold.\n"
                f"2. Formulate clear, natural English instructions for volunteers on the ground to handle routing. "
                f"Explain which gates/corridors are bottlenecks and which alternative gates have low occupancy (< 60%) to redirect traffic to.\n"
                f"3. Provide the response as a JSON object with these keys: 'alerts' (list of strings explaining which gates are overloaded), 'instructions' (a string outlining details, actions, and directions for volunteers)."
            )

            return json.loads(cls._generate_json_content(prompt))
        except Exception as e:
            logger.error(f"Gemini API Error in analyze_crowd: {str(e)}")
            return cls._get_mock_crowd_response(zones, threshold)

    @classmethod
    def translate_query(cls, text: str, fan_lang: str, fan_origin: str, urgency: str, stress: str) -> dict:
        if not api_key_configured or _genai_client is None:
            logger.error("Gemini API key not configured. Real-time translation is required.")
            raise RuntimeError("Gemini API key is not configured. Please set GEMINI_API_KEY for live translation.")

        try:
            prompt = (
                f"You are a multilingual AI assistant for stadium volunteers at the FIFA World Cup.\n"
                f"A fan has walked up to a volunteer and said:\n"
                f"\"{text}\"\n\n"
                f"Context details:\n"
                f"- Declared Language: {fan_lang}\n"
                f"- Fan Origin Country: {fan_origin}\n"
                f"- Input Urgency Level: {urgency}\n"
                f"- Input Stress Level: {stress}\n\n"
                f"Perform the following tasks:\n"
                f"1. Detect the actual language spoken (if not provided, or confirm it).\n"
                f"2. Translate the fan's query into clear English.\n"
                f"3. Analyze if this is a medical or security emergency based on the stress level, urgency, and text content (e.g. chest pain, lost child, injury vs standard restroom/gate direction).\n"
                f"4. Formulate a suggested response from the volunteer in English. IMPORTANT: Adjust tone accordingly. "
                f"If the fan is panicked or has a medical/security emergency, provide a comforting, highly direct response stating help is being called and where they should wait. If it's casual, be friendly and informative.\n"
                f"5. Translate that volunteer response back into the fan's detected language.\n"
                f"6. Return the response as a JSON object with these keys: 'detected_language', 'fan_text_en', 'urgency_analysis', 'suggested_response_en', 'suggested_response_fan_lang'."
            )

            return json.loads(cls._generate_json_content(prompt))
        except Exception as e:
            logger.error(f"Gemini API Error in translate_query: {str(e)}")
            raise

    @classmethod
    def generate_broadcast(cls, scenario: str, target_gates: list, languages: list) -> dict:
        if not api_key_configured or _genai_client is None:
            logger.warning("Gemini API key not configured. Using Mock Broadcast Engine.")
            return cls._get_mock_script_response(scenario, target_gates, languages)

        try:
            prompt = (
                f"You are an operations assistant for stadium announcers and megaphone volunteers at the FIFA World Cup.\n"
                f"We need announcement scripts based on this operational scenario: \"{scenario}\"\n"
                f"Target gates/locations: {', '.join(target_gates)}\n"
                f"Translate this announcement into these target languages: {', '.join(languages)}\n\n"
                f"Format rules:\n"
                f"- The announcement should be short, authoritative, clear, and easy to read.\n"
                f"- Return a JSON object with keys 'scenario' and 'broadcast_scripts' (an object mapping each requested language to its translated script string)."
            )

            response = _genai_client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )

            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini API Error in generate_broadcast: {str(e)}")
            return cls._get_mock_script_response(scenario, target_gates, languages)
