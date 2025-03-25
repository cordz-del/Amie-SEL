# Amie-SEL
Amie-SEL is an advanced, empathetic chatbot designed to engage users in meaningful conversations with a focus on Social Emotional Learning (SEL). The project integrates speech recognition, text-to-speech, and natural language processing using OpenAI and Bot Libre APIs. It also provides a web-based API interface using the Bottle framework.

Features
Conversational AI: Uses Bot Libre for initial responses and OpenAI to refine and enhance them.

Voice Interaction: Implements speech recognition (via speech_recognition) and text-to-speech (via pyttsx3) to support interactive voice-based conversations.

Social Emotional Learning (SEL): Contains age-specific SEL prompts and branching scenarios to help guide reflective conversations.

Dynamic Interaction: Adjusts conversation pace and listening timeout based on the user’s age.

Feedback Collection: Allows users to rate responses and collects feedback for continuous improvement.

Memory & Logging: Saves user preferences and conversation logs to improve contextual interactions over time.

Web API: Exposes a /chat endpoint using the Bottle framework to handle chat messages via HTTP POST requests.

Prerequisites
Python 3.7 or later

Required Python packages:

pyttsx3

openai

speech_recognition

requests

bottle

A valid OpenAI API key (set as the OPENAI_API_KEY environment variable)

Internet connection for accessing external APIs (OpenAI and Bot Libre)
