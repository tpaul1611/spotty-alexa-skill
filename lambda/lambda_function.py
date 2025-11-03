# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging

import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import get_slot_value

from ask_sdk_model import Response

from datetime import datetime, timedelta
from utils import format_time, format_price, get_datetime_vienna, get_utc_noon_vienna
from spottyenergie import spotty_energie_api, handle_api_exception


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Willkommen beim Stromradar, du kannst mich nach dem Strompreis fragen."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class AktuellerPreisIntentHandler(AbstractRequestHandler):
    """Handler for AktuellerPreis Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AktuellerPreis")(handler_input)

    def handle(self, handler_input):
        speak_output = handle_api_exception(self._get_speak_output)()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
    
    def _get_speak_output(self):
        today_prices = spotty_energie_api.get_today_prices()
        if not today_prices:
            return "Ich habe für heute leider keine Preisdaten gefunden."
        
        current_time = get_datetime_vienna()
        positive_prices = [p for p in today_prices if current_time - p.from_time >= timedelta(0)]
        current_price = min(positive_prices, key=lambda p: current_time - p.from_time)
        return f"Im Augenblick beträgt der Strompreis {format_price(current_price.price)} Cent pro Kilowattstunde."


class ZusammenfassungHeuteIntentHandler(AbstractRequestHandler):
    """Handler for ZusammenfassungHeute Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ZusammenfassungHeute")(handler_input)

    def handle(self, handler_input):
        speak_output = handle_api_exception(self._get_speak_output)()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def _get_speak_output(self):
        today_prices = spotty_energie_api.get_today_prices()
        
        if not today_prices:
            return "Ich habe für heute leider keine Preisdaten gefunden."
        
        min_price = min(today_prices, key=lambda p: p.price)
        max_price = max(today_prices, key=lambda p: p.price)

        return (
            f"Heute ist der niedrigste Preis {format_price(min_price.price)} Cent pro Kilowattstunde um {format_time(min_price.from_time)}. "
            f"Der teuerste Preis ist {format_price(max_price.price)} Cent um {format_time(max_price.from_time)}."
        )
    
    
class ZusammenFassungMorgenIntentHandler(AbstractRequestHandler):
    """Handler for ZusammenfassungMorgen Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ZusammenfassungMorgen")(handler_input)

    def handle(self, handler_input):
        speak_output = handle_api_exception(self._get_speak_output)()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def _get_speak_output(self):
        tomorrow_prices = spotty_energie_api.get_tomorrow_prices()

        current_time = get_datetime_vienna()
        utc_noon_vienna = get_utc_noon_vienna().hour
        if current_time.hour <= utc_noon_vienna:
            return f"Die morgigen Preise sind noch nicht verfügbar. Bitte frage nach {utc_noon_vienna} Uhr wieder."
        
        if not tomorrow_prices:
            return "Ich habe für morgen leider keine Preisdaten gefunden."
        
        min_price = min(tomorrow_prices, key=lambda p: p.price)
        max_price = max(tomorrow_prices, key=lambda p: p.price)

        return (
            f"Morgen ist der niedrigste Preis {format_price(min_price.price)} Cent pro Kilowattstunde um {format_time(min_price.from_time)}. "
            f"Der teuerste Preis ist {format_price(max_price.price)} Cent um {format_time(max_price.from_time)}."
        )

    
class ZeitraumHeuteIntentHandler(AbstractRequestHandler):
    """Handler for ZeitraumHeute Intent."""
    def can_handle(self, handler_input: HandlerInput):
        return ask_utils.is_intent_name("ZeitraumHeute")(handler_input)

    def handle(self, handler_input):
        speak_output = handle_api_exception(self._get_speak_output)(handler_input)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def _get_speak_output(self, handler_input: HandlerInput):
        slot_value = get_slot_value(handler_input=handler_input, slot_name="stunden")
        if not slot_value or not str(slot_value).isdigit():
            slot_value = "1"

        hours = max(1, int(slot_value))

        cheapest_hours = spotty_energie_api.get_cheapest_hours_today(hours)
        if not cheapest_hours:
            return "Ich habe für heute leider keine Preisdaten gefunden."
        
        cheapest_hours_start = cheapest_hours[0].from_time
        cheapest_hours_end = cheapest_hours_start + timedelta(hours=hours)
        avg_price = sum(p.price for p in cheapest_hours) / len(cheapest_hours)

        phrase = "günstigste Stunde ist" if hours == 1 else f"{hours} günstigsten Stunden sind"
        return (
            f"Die {phrase} heute von {format_time(cheapest_hours_start)} bis {format_time(cheapest_hours_end)} "
            f"mit einem durchschnittlichen Preis von {format_price(avg_price)} Cent pro Kilowattstunde."
        )
    

class ZeitraumMorgenIntentHandler(AbstractRequestHandler):
    """Handler for ZeitraumMorgen Intent."""
    def can_handle(self, handler_input: HandlerInput):
        return ask_utils.is_intent_name("ZeitraumMorgen")(handler_input)

    def handle(self, handler_input):
        speak_output = handle_api_exception(self._get_speak_output)(handler_input)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

    def _get_speak_output(self, handler_input: HandlerInput):
        current_time = get_datetime_vienna()
        utc_noon_vienna = get_utc_noon_vienna().hour
        if current_time.hour <= utc_noon_vienna:
            return f"Die morgigen Preise sind noch nicht verfügbar. Bitte frage nach {utc_noon_vienna} Uhr wieder."

        slot_value = get_slot_value(handler_input=handler_input, slot_name="stunden")
        if not slot_value or not str(slot_value).isdigit():
            slot_value = "1"

        hours = max(1, int(slot_value))

        cheapest_hours = spotty_energie_api.get_cheapest_hours_tomorrow(hours)
        if not cheapest_hours:
            return "Ich habe für morgen leider keine Preisdaten gefunden."
        
        cheapest_hours_start = cheapest_hours[0].from_time
        cheapest_hours_end = cheapest_hours_start + timedelta(hours=hours)
        avg_price = sum(p.price for p in cheapest_hours) / len(cheapest_hours)
        
        phrase = "günstigste Stunde ist" if hours == 1 else f"{hours} günstigsten Stunden sind"
        return (
            f"Die {phrase} morgen von {format_time(cheapest_hours_start)} bis {format_time(cheapest_hours_end)} "
            f"mit einem durchschnittlichen Preis von {format_price(avg_price)} Cent pro Kilowattstunde."
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Du kannst mich nach dem aktuellen, dem heutigen oder dem morgigen Strompreis fragen. Wie kann ich dir helfen?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Ich wünsche einen spannenden Tag!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, ich bin mir nicht sicher. Du kannst Hallo sagen oder um Hilfe bitten. Was möchtest du tun?"
        reprompt = "Das habe ich nicht verstanden. Wobei kann ich dir helfen?"
        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        speak_output = "Entschuldigung, ich hatte Schwierigkeiten, deine Anfrage zu bearbeiten. Bitte versuche es erneut."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AktuellerPreisIntentHandler())
sb.add_request_handler(ZusammenfassungHeuteIntentHandler())
sb.add_request_handler(ZusammenFassungMorgenIntentHandler())
sb.add_request_handler(ZeitraumHeuteIntentHandler())
sb.add_request_handler(ZeitraumMorgenIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

def lambda_handler(event, context):
    logger.info(f"Invocation event: {event}")
    return sb.lambda_handler()(event, context)
