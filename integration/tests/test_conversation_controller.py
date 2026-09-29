"""Unit tests for Conversation State Machine Controller."""

import pytest
from integration.api.brain_client import BrainClient
from integration.config.integration_config import IntegrationConfig
from integration.controller.conversation_controller import ConversationController
from integration.models.brain_response import ConversationState


def test_conversation_controller_flow():
    config = IntegrationConfig(mock_mode=True)
    client = BrainClient(config)
    states_logged = []

    def on_change(pres):
        states_logged.append(pres.state)

    controller = ConversationController(brain_client=client, config=config, on_state_change=on_change)
    assert controller.current_state == ConversationState.IDLE

    pres = controller.process_text_question("What is Aviral Dhara?", language="hi")
    
    assert ConversationState.PROCESSING in states_logged
    assert ConversationState.THINKING in states_logged
    assert ConversationState.SPEAKING in states_logged
    assert pres.state == ConversationState.SPEAKING
    assert pres.answer != ""

    controller.finish_speaking()
    assert controller.current_state == ConversationState.IDLE


def test_conversation_controller_empty_question():
    config = IntegrationConfig(mock_mode=True)
    controller = ConversationController(config=config)

    pres = controller.process_text_question("", language="en")
    assert pres.state == ConversationState.IDLE
    assert "Please enter a question" in pres.answer


def test_conversation_controller_cancel_to_idle():
    controller = ConversationController(config=IntegrationConfig(mock_mode=True))
    controller.start_listening()
    assert controller.current_state == ConversationState.LISTENING

    reset = controller.cancel_to_idle()
    assert controller.current_state == ConversationState.IDLE
