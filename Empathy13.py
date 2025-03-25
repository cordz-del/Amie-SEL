# Standard libraries
import os
import time
import re
import json

# Third-party libraries
import pyttsx3
import openai
import speech_recognition as sr
import requests

# Bottle imports
from bottle import Bottle, request, response, run


# Ensure OpenAI API Key is set
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

# Replace with your Bot Libre application ID and bot ID
application_id = '5657790313173565017'
bot_id = '56113914'

# Initialize speech recognition and text-to-speech
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Configuration for text-to-speech engine
def configure_tts():
    """
    Configure the text-to-speech engine for Amie's voice settings.
    Sets the voice to a female tone and adjusts the rate and volume.
    """
    voices = engine.getProperty("voices")
    for voice in voices:
        if "female" in voice.name.lower():  # Look for a female voice
            engine.setProperty("voice", voice.id)
            break
    engine.setProperty("rate", 150)  # Normal speech rate
    engine.setProperty("volume", 1.0)  # Maximum volume

# Call TTS configuration during initialization
configure_tts()

# Function to communicate with Bot Libre
def send_message_to_botlibre(message):
    """
    Sends a message to the Bot Libre chatbot and retrieves the response.
    """
    url = 'https://www.botlibre.com/rest/json/chat'
    payload = {
        'application': application_id,
        'instance': bot_id,
        'message': message
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get('message')
        else:
            return f"Error: Unable to communicate with Bot Libre (Status Code: {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def is_quit_command(user_input):
    """
    Checks if the user input is a command to quit or exit the chatbot.
    """
    quit_commands = ["quit", "exit", "goodbye", "bye"]
    return user_input.strip().lower() in quit_commands

# Function to generate responses by combining Bot Libre and OpenAI
def generate_response(user_input):
    """
    Generate a response using Bot Libre and optionally refine it with OpenAI.
    """
    # Get response from Bot Libre
    botlibre_response = send_message_to_botlibre(user_input)
    
    # Use OpenAI to refine the Bot Libre response
    openai_response = openai.Completion.create(
        model="text-davinci-003",
        prompt=botlibre_response,
        max_tokens=150,
        temperature=0.7
    )
    # Return OpenAI-refined response
    return openai_response.choices[0].text.strip()

# Predefined keywords and phrases
FORBIDDEN_TOPICS = ["violence", "hate", "insult", "offensive", "foul language"]
NEGATIVE_KEYWORDS = ["sad", "upset", "depressed", "worthless", "angry", "mad", "jealous", "hate"]
POSITIVE_KEYWORDS = ["happy", "excited", "joyful", "proud", "calm"]
QUIT_KEYWORDS = ["i am done", "goodbye", "leave", "exit", "quit", "bye"]

# SEL prompts and questions categorized by age group
SEL_PROMPTS = {
    "child": [
        "What’s your favorite thing to do with your friends?",
        "Can you tell me about a time you helped someone?",
        "If you could be any animal, which one would you choose and why?"
    ],
    "teen": [
        "What’s a challenge you overcame recently, and how did it feel?",
        "How do you support your friends when they’re feeling down?",
        "If you could invent something to help people, what would it be?"
    ],
    "adult": [
        "What’s something you’ve done recently that you’re proud of?",
        "How do you usually relax after a long day?",
        "What’s a goal you’re working towards, and how can I support you?"
    ]
}

# Helper function: Text-to-speech output
def speak(text, slow=False):
    """
    Converts text to speech for Amie.
    Slows down the speech if the message contains negative or sensitive content.
    """
    print(f"Amie: {text}")
    if slow:
        engine.setProperty("rate", 120)  # Slow down speech for sensitive content
    else:
        engine.setProperty("rate", 150)
    engine.say(text)
    engine.runAndWait()

# Helper function: Recognize user speech input
def listen():
    """
    Captures and transcribes user speech using the microphone.
    Returns the transcribed text or handles errors gracefully if no input is detected.
    """
    with sr.Microphone() as source:
        recognizer.energy_threshold = 300  # Adjust for ambient noise
        print("Listening... Please speak.")
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)  # Timeout set to 10 seconds
            user_input = recognizer.recognize_google(audio)
            print(f"User: {user_input}")
            return user_input.lower()
        except sr.UnknownValueError:
            speak("I didn’t catch that. Could you say it again?")
            return ""
        except sr.WaitTimeoutError:
            speak("I didn’t hear anything. Let’s try again.")
            return ""
        except sr.RequestError as e:
            speak(f"Error with speech recognition: {e}")
            return ""

# Helper function: Extract the name from user input
def extract_name(input_text):
    """
    Extracts the name from user input using a simple pattern match.
    Example: If the input is "my name is John", it will return "John".
    """
    match = re.search(r"my name is (\w+)", input_text)
    return match.group(1) if match else None

# Helper function: Provide age-specific SEL prompts
def get_age_prompt(age):
    """
    Returns a set of predefined prompts based on the user's age group.
    """
    if age <= 12:
        return SEL_PROMPTS["child"]
    elif age <= 18:
        return SEL_PROMPTS["teen"]
    else:
        return SEL_PROMPTS["adult"]

# Main function: Initiates conversation and handles user interactions
def main():
    """
    Core chatbot function to manage the conversation flow.
    Handles user name, age, and provides empathetic, age-appropriate interactions.
    """
    speak("Hello, I am Amie. May I know who I am speaking to?")
    time.sleep(10) # Wait for 5 seconds
    conversation_history = [{"role": "system", "content": "You are a helpful, empathetic chatbot."}]
    name = None
    age = None

    while True:
        user_input = listen()
        if not user_input:
            continue

        if is_quit_command(user_input):
            speak("Goodbye! It was so nice talking to you!")
            break

        if not name:
            name = extract_name(user_input)
            if name:
                speak(f"Nice to meet you, {name}! How old are you?")
            else:
                speak("I didn't catch your name. Could you tell me your name again?")
            continue

        if name and not age:
            if user_input.isdigit():
                age = int(user_input)
                if 5 <= age <= 50:
                    speak(f"Great, {name}! Let's start. How are you feeling today?")
                else:
                    speak("Please tell me your age between 5 and 50.")
                    age = None
            else:
                speak("I didn't catch your age. Could you tell me your age again?")
            continue
        # Handle user silence: Provide a secondary prompt if no response
        if not user_input:
            speak("I noticed you're quiet. Let me ask you this:")
            prompt = random.choice(get_age_prompt(age))  # Select a new prompt based on age
            speak(prompt)
            continue

        # Emotion-aware responses: Analyze input for emotional context
        if any(neg_word in user_input for neg_word in NEGATIVE_KEYWORDS):
            speak("It sounds like you're feeling upset. I'm here to listen. Would you like to share more?", slow=True)
            continue
        elif any(pos_word in user_input for pos_word in POSITIVE_KEYWORDS):
            speak("I'm so glad to hear that! What else is making you feel good today?")
            continue

        # Dynamic response generation
        response = generate_response(user_input, conversation_history)
        speak(response)

        # Suggest a Social Emotional Learning (SEL) scenario if conversation slows
        if user_input in ["i don't know", "not sure", "nothing"]:
            suggest_scenario(age)

        # Gracefully end the conversation if quit command is detected
        if is_quit_command(user_input):
            speak("Goodbye! Remember, you can always come back to chat anytime.")
            break

# Modular function for creating SEL-based age-specific responses
def suggest_scenario(age):
    """
    Suggests and narrates an SEL scenario relevant to the user's age group,
    encouraging engagement and self-reflection.
    """
    prompt = random.choice(get_age_prompt(age))
    speak(f"Here's something to think about: {prompt}")
    if age <= 12:
        speak("Take your time to think and tell me what you'd do.")
    elif age <= 18:
        speak("How would you handle this situation?")
    else:
        speak("What are your thoughts on this scenario?")

# Function to monitor user inactivity during the conversation
def handle_inactivity(last_interaction_time):
    """
    Tracks the time since the user's last interaction and provides prompts or exits
    the conversation after a certain period of silence.
    """
    elapsed_time = time.time() - last_interaction_time
    if elapsed_time > 5 and elapsed_time <= 15:
        speak("I'm still here. Let me know if you want to talk.")
    elif elapsed_time > 15:
        speak("It seems you're busy right now. I'll let you go, but we can talk again soon.")
        return True
    return False

# Modular function for advanced emotion handling
def handle_emotional_response(user_input, age):
    """
    Adjusts tone and content of responses based on the user's emotions,
    providing tailored encouragement or support.
    """
    if any(word in user_input for word in NEGATIVE_KEYWORDS):
        speak("I'm really sorry you're feeling this way. You're not alone, and I'm here for you.", slow=True)
    elif any(word in user_input for word in POSITIVE_KEYWORDS):
        if age <= 12:
            speak("That's so great to hear! What's another fun thing you like to do?")
        elif age <= 18:
            speak("That's awesome! What motivates you to feel that way?")
        else:
            speak("It's wonderful to hear that. Keep that positivity going!")
    else:
        speak("Thank you for sharing that with me.")

# Helper function to log conversation for debugging and refinement
def log_conversation(conversation_log):
    """
    Logs the conversation history for debugging or future training purposes.
    """
    try:
        with open("conversation_log.txt", "a") as log_file:
            for entry in conversation_log:
                log_file.write(f"{entry['role']}: {entry['content']}\n")
            log_file.write("\n--- End of Conversation ---\n")
    except IOError as e:
        print(f"Error logging conversation: {e}")
# Modular function for handling contextual suggestions
def suggest_followup(response_type, age):
    """
    Provides follow-up questions or prompts based on the type of user response.
    Designed to maintain engagement and encourage deeper reflection.
    """
    if response_type == "positive":
        if age <= 12:
            speak("That's great! What's something fun you enjoy doing with your friends?")
        elif age <= 18:
            speak("That's wonderful! How do you think this could inspire others?")
        else:
            speak("That's fantastic! How can you build on this success?")
    elif response_type == "neutral":
        speak("That's interesting. Could you tell me more?")
    elif response_type == "negative":
        speak("I'm sorry you're feeling this way. What can I do to help?", slow=True)

# Error recovery and fallback mechanism
def handle_error(e):
    """
    Handles unexpected errors during execution and provides fallback responses
    to keep the chatbot running smoothly.
    """
    print(f"Error occurred: {e}")
    speak("I'm having a little trouble understanding right now. Could we try again?")

# Advanced SEL interaction: Multi-turn conversation flow
def multi_turn_scenario(age):
    """
    Facilitates a multi-turn interaction where Amie presents a scenario and
    guides the user through multiple reflective steps.
    """
    if age <= 12:
        scenario = "Imagine your best friend is feeling sad because they lost their favorite toy. What would you do to make them feel better?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That's a kind thing to do! How do you think they would feel after that?")
            followup_response = listen()
            if followup_response:
                speak("You're such a thoughtful friend! Always remember, small actions can make a big difference.")
    elif age <= 18:
        scenario = "You notice a classmate sitting alone during lunch. How would you approach them and make them feel included?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That's a great approach. How would you make them feel welcome?")
            followup_response = listen()
            if followup_response:
                speak("That shows great empathy and leadership!")
    else:
        scenario = "A colleague seems stressed and overworked. What could you do to support them without overwhelming them further?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That's thoughtful. How might this improve your working relationship?")
            followup_response = listen()
            if followup_response:
                speak("It's inspiring to see how much you care about others' well-being.")

# Modular helper for re-engaging disengaged users
def reengage_user(age):
    """
    Provides a tailored re-engagement strategy for users who seem less responsive
    or are disengaged from the conversation.
    """
    speak("I noticed it's been a bit quiet. Here's something you can think about:")
    prompt = random.choice(get_age_prompt(age))
    speak(prompt)

# Helper function to validate user age input
def validate_age_input(user_input):
    """
    Validates the age provided by the user and ensures it's within the accepted range.
    """
    if user_input.isdigit():
        age = int(user_input)
        if 5 <= age <= 50:
            return age
    return None

# Main entry point for program execution
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        handle_error(e)

# Social-Emotional Reflection Prompts
SEL_REFLECTION_PROMPTS = {
    "gratitude": [
        "What’s something you’re grateful for today?",
        "Who has been kind to you recently, and how did it make you feel?",
        "What’s a small moment that made you smile this week?"
    ],
    "resilience": [
        "Can you remember a time when you overcame a challenge? How did you do it?",
        "What helps you stay calm when things don’t go your way?",
        "Who or what motivates you when things get tough?"
    ],
    "empathy": [
        "How do you think your actions can make someone else's day better?",
        "Have you ever noticed someone feeling sad? What did you do?",
        "Why do you think it’s important to listen to how others feel?"
    ]
}

# Function to initiate SEL-based reflective prompts
def initiate_reflection(category, age):
    """
    Starts a reflection activity based on a specific SEL category.
    """
    if category in SEL_REFLECTION_PROMPTS:
        prompt = random.choice(SEL_REFLECTION_PROMPTS[category])
        speak(f"Here's something to reflect on: {prompt}")
        user_response = listen()
        if user_response:
            if age <= 12:
                speak("That's a wonderful thought! Thanks for sharing.")
            elif age <= 18:
                speak("That's really insightful. I appreciate you sharing that with me.")
            else:
                speak("Thank you for your thoughtful response. It's great to reflect on these things.")
    else:
        speak("I don't have a reflection ready for that topic right now, but let's keep talking!")
# Function to store and use conversational memory
def update_conversation_memory(conversation_log, user_input, response):
    """
    Updates the conversation memory with the latest user input and chatbot response.
    Helps maintain context and personalize interactions.
    """
    conversation_log.append({"role": "user", "content": user_input})
    conversation_log.append({"role": "assistant", "content": response})

# Function to provide advanced SEL scenarios with branching paths
def advanced_sel_scenario(age):
    """
    Presents a branching SEL scenario where the chatbot guides the user through
    multiple reflective questions based on their responses.
    """
    if age <= 12:
        scenario = "Imagine you see a friend being teased at school. What would you do to help them?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That's a kind way to handle it. How do you think your friend would feel after your help?")
            followup_response = listen()
            if followup_response:
                speak("Great! You showed empathy and stood up for your friend. That's very thoughtful.")
    elif age <= 18:
        scenario = "A friend tells you they’re feeling overwhelmed with homework. How could you support them?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That’s a great idea. How might you balance helping them without feeling overwhelmed yourself?")
            followup_response = listen()
            if followup_response:
                speak("That shows you're both thoughtful and balanced. Great work!")
    else:
        scenario = (
            "Imagine a coworker is struggling to meet a deadline, and you're busy too. "
            "How would you manage helping them while staying on top of your own work?"
        )
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("That’s a helpful way to approach it. How do you think this would impact your working relationship?")
            followup_response = listen()
            if followup_response:
                speak("Excellent! Supporting others while managing your own responsibilities shows leadership and empathy.")

# Function to generate SEL-specific responses dynamically
def generate_sel_response(user_input, category, age):
    """
    Dynamically generates an SEL-focused response based on user input,
    the specified SEL category, and their age group.
    """
    try:
        prompt = f"Provide an empathetic and age-appropriate response for the SEL category '{category}'. User said: '{user_input}'"
        conversation_history = [{"role": "system", "content": "You are a helpful, empathetic assistant."}]
        conversation_history.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=200,
            temperature=0.7
        )
        chatbot_reply = response.choices[0].message.content.strip()
        speak(chatbot_reply)
    except Exception as e:
        handle_error(e)

# Advanced error handling with fallback strategies
def handle_error(e):
    """
    Provides robust error handling and fallback strategies to ensure
    the chatbot remains functional during unexpected issues.
    """
    print(f"An error occurred: {e}")
    speak("Oops! I ran into a small issue. Let me ask you something else instead.")
    speak("What’s something that made you smile recently?")

# Personalized follow-up based on conversational context
def personalized_followup(conversation_log):
    """
    Generates a follow-up prompt tailored to the ongoing conversation context.
    Ensures the chatbot maintains relevance and engagement.
    """
    if not conversation_log:
        speak("Let's start fresh! How can I help you today?")
        return

    last_user_input = conversation_log[-2]["content"] if len(conversation_log) >= 2 else ""
    last_response = conversation_log[-1]["content"] if len(conversation_log) >= 1 else ""

    if "feeling" in last_user_input:
        speak("Earlier you mentioned how you're feeling. Would you like to talk more about that?")
    elif "friend" in last_user_input:
        speak("You mentioned a friend earlier. How’s your relationship with them?")
    else:
        speak("Let’s keep the conversation going! What’s on your mind now?")

# Advanced SEL prompt rotation
def rotate_sel_prompts(conversation_log, age):
    """
    Cycles through a predefined set of SEL prompts to maintain variety and
    engagement across multiple interactions.
    """
    used_prompts = [entry["content"] for entry in conversation_log if entry["role"] == "assistant"]
    available_prompts = [p for p in get_age_prompt(age) if p not in used_prompts]

    if available_prompts:
        prompt = random.choice(available_prompts)
        speak(f"Here’s a question for you: {prompt}")
    else:
        speak("It seems we’ve covered a lot of topics. Is there something specific you’d like to talk about?")

# Logging and session termination
def log_and_terminate(conversation_log):
    """
    Logs the entire session and provides a closing message before terminating.
    """
    try:
        log_conversation(conversation_log)
        speak("Thank you for talking with me today. Remember, I'm always here if you need me.")
    except Exception as e:
        print(f"Error during termination: {e}")
        speak("Goodbye for now! I'll see you next time.")

# Final main function for session integration
def main():
    """
    Executes the chatbot session, including dynamic responses, SEL interactions,
    and session handling.
    """
    conversation_log = []
    speak("Hi there! I’m Amie, your friendly chatbot. Can you tell me your name?")
    name = None
    age = None

    while True:
        try:
            user_input = listen()

            # Handle empty input
            if not user_input:
                reengage_user(age)
                continue

            # Quit if user requests
            if is_quit_command(user_input):
                log_and_terminate(conversation_log)
                break

            # Extract name
            if not name:
                name = extract_name(user_input)
                if name:
                    speak(f"Nice to meet you, {name}! How old are you?")
                else:
                    speak("I didn't catch your name. Can you tell me again?")
                continue

            # Extract and validate age
            if name and not age:
                age = validate_age_input(user_input)
                if age:
                    speak(f"Thanks, {name}! Let’s talk about something interesting.")
                else:
                    speak("Can you tell me your age again? It should be between 5 and 50.")
                continue

            # Handle dynamic SEL prompts
            rotate_sel_prompts(conversation_log, age)

            # Generate responses and update memory
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)

        except Exception as e:
            handle_error(e)
# Function for storing long-term memory
def save_user_preferences(name, age):
    """
    Saves user preferences (name and age) for future sessions.
    Data is stored in a simple local file named 'user_preferences.json'.
    """
    import json

    user_data = {"name": name, "age": age}
    try:
        with open("user_preferences.json", "w") as f:
            json.dump(user_data, f)
        print("User preferences saved successfully.")
    except IOError as e:
        print(f"Error saving user preferences: {e}")

# Function to load user preferences
def load_user_preferences():
    """
    Loads user preferences (name and age) from 'user_preferences.json' if available.
    Returns the data or None if the file doesn't exist or has errors.
    """
    import json

    try:
        with open("user_preferences.json", "r") as f:
            user_data = json.load(f)
        print("User preferences loaded successfully.")
        return user_data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading user preferences: {e}")
        return None

# Enhanced emotion-based SEL scenarios
def emotion_branching_scenario(user_input, age):
    """
    Guides the conversation based on emotional keywords in the user's input.
    Provides tailored prompts for negative and positive emotions.
    """
    if any(word in user_input for word in NEGATIVE_KEYWORDS):
        speak("I’m sorry you’re feeling this way. Would you like to tell me more?")
        followup = listen()
        if followup:
            if age <= 12:
                speak("Talking about it is a good step. What could make you feel a little better?")
            elif age <= 18:
                speak("That’s tough. What are some things you usually do to feel better?")
            else:
                speak("It’s okay to feel this way. Sometimes sharing with a trusted person can help.")
    elif any(word in user_input for word in POSITIVE_KEYWORDS):
        speak("That’s wonderful! Let’s keep the good vibes going.")
        if age <= 12:
            speak("What’s one thing that made you laugh today?")
        elif age <= 18:
            speak("What’s something exciting you’re looking forward to?")
        else:
            speak("What’s a recent accomplishment you feel proud of?")
    else:
        speak("Thank you for sharing that with me. Let’s keep talking!")

# Function to recall user preferences
def greet_user_with_memory():
    """
    Greets the user with their saved preferences if available.
    Prompts for new information if preferences are not found.
    """
    user_data = load_user_preferences()
    if user_data:
        name = user_data.get("name", "there")
        age = user_data.get("age")
        speak(f"Welcome back, {name}! It's great to talk to you again.")
        return name, age
    else:
        speak("Hi there! I’m Amie, your friendly chatbot. Can you tell me your name?")
        return None, None

# Function to guide the user into SEL exercises
def guided_sel_exercise(category, age):
    """
    Leads the user through a guided SEL exercise based on the specified category.
    """
    if category == "gratitude":
        speak("Let’s try a gratitude exercise. Think about something you’re thankful for today.")
        user_response = listen()
        if user_response:
            if age <= 12:
                speak("That’s so wonderful to hear. Gratitude can make us feel happier!")
            elif age <= 18:
                speak("That’s a great thought! How could you show gratitude for it?")
            else:
                speak("Thank you for sharing. Gratitude is a great way to reflect positively.")
    elif category == "resilience":
        speak("Let’s talk about resilience. Think of a time when you overcame a challenge.")
        user_response = listen()
        if user_response:
            speak("That’s amazing. What did you learn about yourself from that experience?")
    elif category == "empathy":
        speak("Let’s practice empathy. Imagine a friend is feeling sad. What would you do to help?")
        user_response = listen()
        if user_response:
            speak("That’s thoughtful. Showing empathy helps build strong friendships.")

# Real-time feedback system
def provide_feedback(user_input):
    """
    Provides immediate feedback to the user based on the tone of their input.
    """
    if any(word in user_input for word in NEGATIVE_KEYWORDS):
        speak("You’re doing great by sharing how you feel. What’s one small thing that could help right now?")
    elif any(word in user_input for word in POSITIVE_KEYWORDS):
        speak("I’m glad to hear that! Let’s keep the good energy going.")
    else:
        speak("That’s interesting! Can you tell me more?")

# Enhanced re-engagement for inactivity
def reengage_with_memory(name, age):
    """
    Re-engages a disengaged user by recalling their name and providing age-appropriate prompts.
    """
    if name and age:
        speak(f"{name}, it’s been a little quiet. How are you feeling?")
    else:
        speak("It’s been a little quiet. Let’s keep talking!")

# Comprehensive logging for debugging and training
def log_debugging_data(conversation_log, event_type):
    """
    Logs detailed debugging information, including conversation context and events.
    """
    try:
        with open("debug_log.txt", "a") as debug_file:
            debug_file.write(f"Event: {event_type}\n")
            for entry in conversation_log:
                debug_file.write(f"{entry['role']}: {entry['content']}\n")
            debug_file.write("\n--- End of Debug Data ---\n")
    except IOError as e:
        print(f"Error logging debugging data: {e}")

# Refined session end logic with memory update
def end_session_with_memory(conversation_log, name, age):
    """
    Ends the session gracefully, logs the conversation, and saves user preferences.
    """
    log_conversation(conversation_log)
    if name and age:
        save_user_preferences(name, age)
    speak("It was so nice talking to you today. Have a wonderful day!")
# Function to guide users through goal-setting exercises
def guided_goal_setting(name, age):
    """
    Helps the user set a goal and create actionable steps to achieve it.
    Uses age-appropriate language and encouragement.
    """
    speak(f"{name}, let’s work on setting a goal together.")
    speak("What’s one thing you’d like to achieve soon?")
    user_response = listen()

    if user_response:
        if age <= 12:
            speak("That’s a great goal! What’s one small step you can take to get started?")
        elif age <= 18:
            speak("That’s an ambitious goal! What resources or support could help you achieve it?")
        else:
            speak("That’s a meaningful goal. What’s your first step, and how can I help keep you on track?")

        followup_response = listen()
        if followup_response:
            speak("That’s a fantastic start! Remember, progress takes time, and you’re on the right path.")

# Advanced SEL prompts with multi-step branching
def multi_step_sel_branching(name, age):
    """
    Facilitates advanced SEL scenarios with multiple steps,
    guiding the user through reflective thinking and decision-making.
    """
    speak(f"{name}, let’s imagine a scenario together.")
    if age <= 12:
        scenario = "You see a classmate struggling to open their lunchbox. What would you do to help them?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("How do you think they would feel if you helped them?")
            followup_response = listen()
            if followup_response:
                speak("You’re showing great kindness and thoughtfulness!")
    elif age <= 18:
        scenario = "A friend posts something online that upsets you. How would you approach them about it?"
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("What could you say to express your feelings without hurting theirs?")
            followup_response = listen()
            if followup_response:
                speak("That’s a mature and empathetic way to handle the situation.")
    else:
        scenario = (
            "Your coworker takes credit for a project you worked hard on. "
            "How would you address this while staying professional?"
        )
        speak(scenario)
        user_response = listen()
        if user_response:
            speak("What’s a constructive way to ensure your efforts are recognized?")
            followup_response = listen()
            if followup_response:
                speak("That’s a balanced and professional approach. Great thinking!")

# Enhanced memory management with customizable options
def update_user_memory(name, age, preferences=None):
    """
    Updates the user's memory with customizable preferences.
    """
    import json

    user_data = {"name": name, "age": age, "preferences": preferences or {}}
    try:
        with open("user_preferences.json", "w") as f:
            json.dump(user_data, f)
        print("User memory updated successfully.")
    except IOError as e:
        print(f"Error updating user memory: {e}")

# Load memory with fallback handling
def load_memory_with_fallback(file_path="user_preferences.json"):
    """
    Load user memory from a JSON file. If the file is missing, return default values.
    """
    try:
        # Attempt to open and load the user preferences file
        with open(file_path, "r") as f:
            memory = json.load(f)
            # Extract name and age from the memory
            name = memory.get("name", "there")  # Default to "there" if no name is found
            age = memory.get("age")  # Age may be None if not provided
            return name, age
    except FileNotFoundError:
        # Handle the case where the file does not exist
        print(f"Error loading user preferences: {file_path} not found. Using defaults.")
        return "Guest", None
    except json.JSONDecodeError:
        # Handle the case where the file exists but contains invalid JSON
        print(f"Error loading user preferences: {file_path} contains invalid JSON. Using defaults.")
        return "Guest", None

# Context-aware re-engagement
def context_aware_reengagement(conversation_log, name, age):
    """
    Re-engages the user by referencing recent topics or user-specific data.
    """
    if conversation_log:
        last_user_input = conversation_log[-2]["content"] if len(conversation_log) >= 2 else None
        if last_user_input and "feeling" in last_user_input:
            speak("Earlier, we talked about how you’re feeling. Would you like to continue?")
        elif last_user_input and "friend" in last_user_input:
            speak("We were discussing your friends earlier. How are they doing?")
        else:
            speak(f"Let’s pick up where we left off, {name}. What’s on your mind?")
    else:
        speak(f"{name}, it’s been quiet. How about we talk about something new?")

# Function to manage advanced user preferences
def manage_user_preferences():
    """
    Allows the user to update or review their preferences during the session.
    """
    speak("Would you like to update your preferences, like your name or age?")
    user_response = listen()
    if "yes" in user_response:
        speak("Okay, let’s update your preferences. What’s your name?")
        name = listen()
        speak(f"Thanks, {name}. And how old are you?")
        age_response = listen()
        age = validate_age_input(age_response)
        if age:
            update_user_memory(name, age)
            speak(f"Your preferences have been updated. Thanks, {name}!")
        else:
            speak("I couldn’t catch that. Let’s try updating later.")
    else:
        speak("No problem! Let me know if you’d like to update them later.")

# Function to gracefully reset the session
def reset_session(conversation_log):
    """
    Resets the session while retaining user preferences.
    """
    speak("Would you like to start fresh while keeping your preferences?")
    user_response = listen()
    if "yes" in user_response:
        conversation_log.clear()
        speak("Great! Let’s start over. What would you like to talk about?")
    else:
        speak("Okay, we’ll keep going from here.")

# Expanded SEL categories
EXPANDED_SEL_CATEGORIES = {
    "self-awareness": [
        "What’s one thing you’re really good at?",
        "How do you feel when you achieve something important?",
        "What’s something you’d like to improve about yourself?"
    ],
    "self-management": [
        "How do you stay calm when things don’t go your way?",
        "What’s a strategy you use to stay focused on your goals?",
        "How do you handle stress when you feel overwhelmed?"
    ],
    "social awareness": [
        "What’s something interesting you’ve learned about someone else recently?",
        "How do you know when someone needs help, even if they don’t say it?",
        "Why is it important to appreciate other people’s differences?"
    ],
}

# Function to introduce expanded SEL exercises
def expanded_sel_exercise(category, age):
    """
    Facilitates advanced SEL exercises from expanded categories.
    """
    if category in EXPANDED_SEL_CATEGORIES:
        prompt = random.choice(EXPANDED_SEL_CATEGORIES[category])
        speak(f"Let’s think about this: {prompt}")
        user_response = listen()
        if user_response:
            speak("Thank you for sharing your thoughts. Let’s keep exploring!")
    else:
        speak("I don’t have an exercise for that topic yet, but let’s keep talking!")
# Function to handle multi-turn SEL exercises dynamically
def dynamic_multi_turn_exercise(category, age):
    """
    Engages the user in a multi-turn SEL exercise based on the chosen category.
    Adjusts prompts and responses dynamically to ensure engagement.
    """
    if category == "self-awareness":
        speak("Let’s work on understanding ourselves better.")
        speak("What’s one thing that makes you really happy?")
        user_response = listen()
        if user_response:
            speak("That’s great to hear! Why do you think it makes you so happy?")
            followup_response = listen()
            if followup_response:
                speak("You’ve shared something meaningful about yourself. Great job!")
    elif category == "self-management":
        speak("Let’s practice staying calm and focused.")
        speak("What’s a time when you stayed calm in a tough situation?")
        user_response = listen()
        if user_response:
            speak("That sounds like a challenging moment. How did you manage to stay calm?")
            followup_response = listen()
            if followup_response:
                speak("You showed great self-control in that situation. Keep it up!")
    elif category == "social awareness":
        speak("Let’s think about how we connect with others.")
        speak("Have you noticed someone who needed help recently?")
        user_response = listen()
        if user_response:
            speak("That’s thoughtful of you to notice. What did you do to help them?")
            followup_response = listen()
            if followup_response:
                speak("Helping others is such an important skill. You’re doing great!")

# Function for real-time goal tracking
def track_user_goal(goal, progress_log):
    """
    Tracks user progress toward their goals and provides encouragement.
    """
    speak(f"You mentioned your goal is: {goal}. How is it going?")
    user_response = listen()
    if "good" in user_response or "progress" in user_response:
        speak("That’s fantastic! Keep up the great work.")
        progress_log.append({"goal": goal, "status": "in progress"})
    elif "stuck" in user_response or "not good" in user_response:
        speak("That’s okay. Every step forward counts. What can we do to get back on track?")
        progress_log.append({"goal": goal, "status": "needs support"})
    else:
        speak("Let’s revisit this goal later. You’re still making progress by thinking about it!")

# Expanded age-specific SEL re-engagement
def age_specific_reengagement(name, age):
    """
    Re-engages the user with tailored prompts based on their age.
    """
    if age <= 12:
        speak(f"{name}, what’s something fun you’ve done recently?")
    elif age <= 18:
        speak(f"{name}, what’s something interesting you’ve learned or experienced lately?")
    else:
        speak(f"{name}, what’s a recent success or challenge you’d like to talk about?")

# Function to create dynamic SEL-based branching scenarios
def branching_scenario_with_choices(age):
    """
    Engages the user in a branching SEL scenario where they choose actions
    and see how those choices affect the outcome.
    """
    if age <= 12:
        speak("You see a friend drop their lunch on the floor. What would you do?")
        speak("Would you: 1) Offer to share your lunch, or 2) Help them clean up?")
        choice = listen()
        if "1" in choice or "share" in choice:
            speak("That’s so generous of you! Your friend would really appreciate that.")
        elif "2" in choice or "help" in choice:
            speak("Helping to clean up shows you care. Great choice!")
        else:
            speak("Both actions are kind and thoughtful. Well done!")
    elif age <= 18:
        speak("A friend is struggling with a group project and asks for your help.")
        speak("Would you: 1) Offer to help with their part, or 2) Share tips to help them improve?")
        choice = listen()
        if "1" in choice or "help" in choice:
            speak("That’s very supportive of you! It’s great to help a friend in need.")
        elif "2" in choice or "tips" in choice:
            speak("That’s a smart way to help your friend learn and grow. Great choice!")
        else:
            speak("Both actions are thoughtful. You’re being a great friend!")
    else:
        speak("You notice a coworker struggling with a task they don’t understand.")
        speak("Would you: 1) Offer to mentor them, or 2) Suggest resources they could use?")
        choice = listen()
        if "1" in choice or "mentor" in choice:
            speak("Mentoring is a great way to build relationships and share knowledge.")
        elif "2" in choice or "resources" in choice:
            speak("Providing resources empowers them to grow independently. Great choice!")
        else:
            speak("Both actions show leadership and empathy. Excellent thinking!")

# Function for summarizing user progress and session highlights
def summarize_session(conversation_log, name, goals):
    """
    Summarizes the session, including user progress and SEL achievements.
    """
    speak(f"{name}, here’s what we’ve covered today:")
    for entry in conversation_log:
        if entry["role"] == "user":
            speak(f"You shared: {entry['content']}")
        elif entry["role"] == "assistant":
            speak(f"I responded with: {entry['content']}")
    if goals:
        speak("Here are your goals and progress:")
        for goal in goals:
            status = goal.get("status", "ongoing")
            speak(f"Goal: {goal['goal']}, Status: {status}")
    speak("You’ve made great progress! I’m so proud of you.")

# Function to wrap up the session with actionable takeaways
def wrap_up_session(conversation_log, name, goals):
    """
    Concludes the session with encouragement and actionable takeaways.
    """
    summarize_session(conversation_log, name, goals)
    speak("Before we go, is there anything else you’d like to talk about?")
    user_response = listen()
    if user_response and "no" not in user_response.lower():
        speak("Okay! Let’s keep chatting for a bit longer.")
    else:
        speak(f"Thanks for chatting with me, {name}! Remember, I’m always here when you need me.")
# Function to create emotion-based branching scenarios
def emotion_adaptive_scenario(user_input, age):
    """
    Adjusts the SEL scenario based on the emotional tone detected in the user's input.
    Provides calming or motivating exercises depending on the emotion.
    """
    if any(word in user_input for word in NEGATIVE_KEYWORDS):
        speak("It sounds like you’re feeling a bit down. Let’s do something calming together.")
        if age <= 12:
            speak("Imagine you’re in a cozy fort filled with your favorite things. What would you have in there?")
        elif age <= 18:
            speak("Think about a peaceful place that makes you feel calm. Where would it be?")
        else:
            speak("Take a deep breath and picture a moment when you felt truly at peace. What made it so calming?")
    elif any(word in user_input for word in POSITIVE_KEYWORDS):
        speak("You’re feeling good today! Let’s build on that positivity.")
        if age <= 12:
            speak("What’s something fun you want to do later?")
        elif age <= 18:
            speak("What’s a recent success that made you proud?")
        else:
            speak("What’s something exciting you’re looking forward to this week?")
    else:
        speak("Thanks for sharing! Let’s keep talking about what’s on your mind.")

# Function to guide users through a grounding exercise
def grounding_exercise(age):
    """
    Leads the user through a grounding exercise to help them manage stress or anxiety.
    Adjusts the language based on age.
    """
    speak("Let’s try a grounding exercise to feel calm and focused.")
    if age <= 12:
        speak("Can you name five things you see around you?")
        listen()
        speak("Now, name four things you can touch.")
        listen()
        speak("Great! Now, name three sounds you hear.")
        listen()
        speak("You’re doing amazing! Let’s take a big breath together.")
    elif age <= 18:
        speak("Take a moment and name five things you see right now.")
        listen()
        speak("Now, focus on four things you can physically feel.")
        listen()
        speak("Great! Name three sounds you can hear nearby.")
        listen()
        speak("Awesome work! Let’s take a deep, calming breath together.")
    else:
        speak("Start by identifying five objects around you.")
        listen()
        speak("Next, focus on four physical sensations you’re aware of.")
        listen()
        speak("Now, name three sounds in your environment.")
        listen()
        speak("You’re doing great. Let’s pause for a deep, grounding breath.")

# Adaptive interaction based on conversation pace
def adjust_conversation_pace(user_input, conversation_log):
    """
    Dynamically adjusts the pace of the conversation based on user engagement.
    """
    if len(user_input.split()) < 3:
        speak("It seems like you might need more time to think. No rush, take your time.")
    elif len(conversation_log) >= 5:
        speak("We’ve covered a lot! Let’s take a moment to reflect. What stood out to you most?")
    else:
        speak("I’m here to keep the conversation going. What’s on your mind?")

# Function to explore future-oriented SEL exercises
def future_planning_exercise(name, age):
    """
    Encourages the user to think about their future and set long-term aspirations.
    Adjusts the prompts to match the user's age and interests.
    """
    speak(f"{name}, let’s think about your future goals.")
    if age <= 12:
        speak("What’s something you dream of being or doing when you grow up?")
    elif age <= 18:
        speak("Where do you see yourself in five years? What would you like to achieve?")
    else:
        speak("What’s a long-term goal that’s important to you?")
    user_response = listen()
    if user_response:
        speak(f"That’s a wonderful goal, {name}. What’s one small step you can take today to move closer to it?")

# Function to check and respond to user fatigue
def detect_user_fatigue(conversation_log):
    """
    Monitors user responses for signs of fatigue or disengagement.
    Offers to adjust the conversation or take a short break if needed.
    """
    if len(conversation_log) > 10:
        speak("It seems like we’ve been chatting for a while. Would you like to keep going or take a short break?")
        user_response = listen()
        if "break" in user_response:
            speak("Alright, let’s take a quick pause. I’ll be here when you’re ready to continue.")
            return True
        elif "keep going" in user_response or "no" in user_response:
            speak("Great! Let’s keep going. What would you like to talk about?")
        else:
            speak("No problem! Let me know if you need a break anytime.")
    return False

# Function to incorporate mindfulness techniques
def mindfulness_activity(age):
    """
    Guides the user through a mindfulness exercise to help them focus and relax.
    Adjusts based on age for simplicity or depth.
    """
    speak("Let’s try a mindfulness activity together.")
    if age <= 12:
        speak("Close your eyes and imagine your favorite place. What does it look like?")
    elif age <= 18:
        speak("Take a moment to focus on your breathing. Feel the air as you inhale and exhale.")
    else:
        speak("Close your eyes and take a deep breath. Focus on how your body feels with each breath.")
    user_response = listen()
    if user_response:
        speak("That’s great! Mindfulness can help us feel calm and focused.")

# Function for deeper multi-step branching interactions
def multi_step_branching_exercise(age):
    """
    Offers a more complex, multi-step branching scenario that adapts based on the user’s choices.
    """
    speak("Let’s imagine a challenging situation together.")
    if age <= 12:
        speak("You’re playing a game, and a friend isn’t following the rules. What would you do?")
        speak("Would you: 1) Talk to them about the rules, or 2) Ask an adult for help?")
        choice = listen()
        if "1" in choice or "talk" in choice:
            speak("That’s a good idea! Talking can help solve the problem.")
        elif "2" in choice or "ask" in choice:
            speak("Asking an adult is a responsible choice. Great thinking!")
        else:
            speak("Both options are helpful. Good job!")
    elif age <= 18:
        speak("You’re leading a group project, but one member isn’t contributing. What would you do?")
        speak("Would you: 1) Talk to them privately, or 2) Adjust their tasks to make it easier?")
        choice = listen()
        if "1" in choice or "privately" in choice:
            speak("That’s a mature way to handle the situation. Well done!")
        elif "2" in choice or "adjust" in choice:
            speak("Being flexible shows great leadership. Nice job!")
        else:
            speak("Both approaches are thoughtful. Keep it up!")
    else:
        speak("You’re working on a team project, and deadlines are approaching. What would you do?")
        speak("Would you: 1) Take on more tasks yourself, or 2) Delegate tasks more effectively?")
        choice = listen()
        if "1" in choice or "take on" in choice:
            speak("Taking responsibility is admirable, but don’t forget to ask for help when needed!")
        elif "2" in choice or "delegate" in choice:
            speak("Delegating tasks effectively shows strong leadership. Great choice!")
        else:
            speak("Both actions reflect your dedication and thoughtfulness. Excellent work!")
# Function for open-ended problem-solving exercises
def open_ended_problem_solving(name, age):
    """
    Encourages the user to think creatively and critically about solving real-world problems.
    Adjusts language and scenarios based on the user's age.
    """
    speak(f"{name}, let’s try solving a fun problem together!")
    if age <= 12:
        speak("Imagine your friend is feeling left out during recess. What could you do to make them feel included?")
    elif age <= 18:
        speak("You notice that a group project isn’t going well because of disagreements. How would you handle it?")
    else:
        speak("A colleague is struggling to keep up with deadlines, and it’s affecting the team. How would you support them?")
    user_response = listen()
    if user_response:
        speak(f"That’s a thoughtful approach, {name}. It’s great to think about how your actions affect others!")

# Final session wrap-up function
def session_wrap_up(conversation_log, name, age):
    """
    Provides a closing summary of the session and ensures the user feels heard and supported.
    """
    speak("Before we finish, let’s reflect on what we talked about today.")
    for entry in conversation_log:
        if entry["role"] == "user":
            speak(f"You shared: {entry['content']}")
        elif entry["role"] == "assistant":
            speak(f"I responded with: {entry['content']}")
    speak(f"{name}, you’ve done an amazing job today! Keep being your wonderful self.")
    if age <= 12:
        speak("I’m so proud of how kind and thoughtful you are!")
    elif age <= 18:
        speak("You’re showing so much growth and maturity. Keep it up!")
    else:
        speak("You’re a great example of resilience and thoughtfulness. Well done!")
    speak("Thank you for spending time with me. I hope to talk to you again soon!")

# Main function for integrating all features
def main():
    """
    Executes the chatbot session, integrating SEL exercises, emotion-based branching,
    memory, and dynamic user interaction.
    """
    conversation_log = []
    name, age = load_memory_with_fallback()
    goals = []

    if not name or not age:
        name = None
        age = None
        while not name:
            speak("Can you tell me your name?")
            user_input = listen()
            name = extract_name(user_input)
            if not name:
                speak("I didn’t catch that. Could you say your name again?")
        while not age:
            speak("Can you tell me your age? It should be between 5 and 50.")
            user_input = listen()
            age = validate_age_input(user_input)
            if not age:
                speak("I didn’t catch that. Could you tell me your age again?")
        update_user_memory(name, age)

    speak(f"Hi {name}! It’s great to meet you. Let’s talk!")
    while True:
        user_input = listen()
        if not user_input:
            reengage_user(age)
            continue
        if is_quit_command(user_input):
            session_wrap_up(conversation_log, name, age)
            break

        if detect_user_fatigue(conversation_log):
            continue

        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            future_planning_exercise(name, age)
        else:
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)
# Function to dynamically adjust listening time based on age
def get_listening_timeout(age):
    """
    Determines the listening timeout based on the user's age group.
    Younger users are given more time to respond.
    """
    if age is None:
        # Default timeout before age is determined
        return 10
    elif age <= 12:
        return 15  # Younger children may need more time
    elif age <= 20:
        return 12  # Teens may need slightly less time
    else:
        return 10  # Adults can handle shorter timeouts

# Updated listen function with dynamic timeout
def listen_with_dynamic_timeout(age):
    """
    Listens to the user's input using a microphone with a timeout
    that dynamically adjusts based on the user's age group.
    """
    timeout = get_listening_timeout(age)
    print(f"Listening with a timeout of {timeout} seconds...")
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)
            user_input = recognizer.recognize_google(audio)
            print(f"User: {user_input}")
            return user_input.lower()
        except sr.UnknownValueError:
            speak("I didn’t catch that. Could you say it again?")
            return ""
        except sr.WaitTimeoutError:
            speak("I didn’t hear anything. Let’s try again.")
            return ""

# Function to interact and handle dynamic timeout based on age
def interact_with_dynamic_listening(conversation_log, name, age):
    """
    Main interaction loop that adjusts listening time dynamically based on age.
    """
    while True:
        user_input = listen_with_dynamic_timeout(age)
        if not user_input:
            # Handle cases of no input
            speak("It’s okay, take your time. Let me know when you’re ready.")
            continue

        # Quit if user signals the end of the session
        if is_quit_command(user_input):
            session_wrap_up(conversation_log, name, age)
            break

        # Handle user responses and generate appropriate reactions
        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            future_planning_exercise(name, age)
        else:
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)

# Main function updated to include dynamic listening timeout
def main():
    """
    Executes the chatbot session, now with dynamic listening timeouts
    based on age groups.
    """
    conversation_log = []
    name, age = load_memory_with_fallback()

    if not name or not age:
        name = None
        age = None
        while not name:
            speak("Can you tell me your name?")
            user_input = listen_with_dynamic_timeout(None)
            name = extract_name(user_input)
            if not name:
                speak("I didn’t catch that. Could you say your name again?")
        while not age:
            speak("Can you tell me your age? It should be between 5 and 50.")
            user_input = listen_with_dynamic_timeout(None)
            age = validate_age_input(user_input)
            if not age:
                speak("I didn’t catch that. Could you tell me your age again?")
        update_user_memory(name, age)

    speak(f"Hi {name}! It’s great to meet you. Let’s talk!")
    interact_with_dynamic_listening(conversation_log, name, age)

# Function to summarize changes for dynamic listening
def explain_dynamic_listening():
    """
    Explains the dynamic listening feature to the user for better clarity.
    """
    speak("Just so you know, I’ll give you extra time to respond based on your age.")
    speak("Younger users get more time to think and reply. Let me know if you’re ready!")

# Entry point for the program
if __name__ == "__main__":
    explain_dynamic_listening()  # Ensure the dynamic listening explanation is executed
    try:
        main()  # Start the chatbot
    except Exception as e:
        handle_error(e)

# Function to collect feedback from the user
def collect_feedback(conversation_log, response):
    """
    Prompts the user for feedback on the chatbot's response.
    Stores the feedback in the conversation log for later analysis.
    """
    speak("How helpful was my response on a scale of 1 to 5?")
    rating_input = listen()
    try:
        rating = int(rating_input)
        if 1 <= rating <= 5:
            speak("Thank you! Would you like to add a comment?")
            comment = listen()
            feedback_entry = {
                "response": response,
                "rating": rating,
                "comment": comment.strip() if comment else None,
            }
            conversation_log.append({"role": "feedback", "content": feedback_entry})
            speak("Your feedback is valuable. Thank you!")
        else:
            speak("Please provide a rating between 1 and 5.")
            return collect_feedback(conversation_log, response)
    except ValueError:
        speak("I didn’t catch that. Please provide a number between 1 and 5.")
        return collect_feedback(conversation_log, response)

# Function to analyze feedback
def analyze_feedback(conversation_log):
    """
    Analyzes the feedback collected during the session.
    Calculates the average rating and highlights key comments.
    """
    feedback_entries = [
        entry["content"]
        for entry in conversation_log
        if entry["role"] == "feedback"
    ]
    if not feedback_entries:
        return None

    total_rating = sum(fb["rating"] for fb in feedback_entries)
    avg_rating = total_rating / len(feedback_entries)

    comments = [fb["comment"] for fb in feedback_entries if fb["comment"]]

    return {
        "average_rating": avg_rating,
        "comments": comments,
        "total_feedback": len(feedback_entries),
    }

# Function to wrap up the session with feedback analysis
def session_feedback_summary(conversation_log):
    """
    Provides a summary of feedback at the end of the session.
    """
    feedback_summary = analyze_feedback(conversation_log)
    if feedback_summary:
        avg_rating = feedback_summary["average_rating"]
        speak(f"Thank you for your feedback! My average rating this session was {avg_rating:.1f}.")
        if feedback_summary["comments"]:
            speak("Here are some comments I received:")
            for comment in feedback_summary["comments"]:
                speak(f"User said: {comment}")
    else:
        speak("I didn’t receive any feedback this session. I hope to improve next time!")

# Modify the interaction loop to include feedback collection
def interact_with_feedback(conversation_log, name, age):
    """
    Main interaction loop that includes feedback collection.
    """
    while True:
        user_input = listen_with_dynamic_timeout(age)
        if not user_input:
            speak("It’s okay, take your time. Let me know when you’re ready.")
            continue

        if is_quit_command(user_input):
            session_feedback_summary(conversation_log)
            break

        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            future_planning_exercise(name, age)
        else:
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)

            # Collect feedback for the generated response
            collect_feedback(conversation_log, response)

# Inserted Code for Social and Emotional Learning (SEL)
# ------------------------------------------------------

# Expanded SEL categories and prompts for each age group
EXPANDED_SEL_PROMPTS = {
    "child": {
        "self-awareness": [
            "What’s something you’re really good at?",
            "What makes you smile the most?",
            "Can you think of a time when you were really brave?"
        ],
        "self-management": [
            "How do you calm yourself down when you feel upset?",
            "What’s one way you can stay focused on something important?",
            "What helps you when you feel nervous?"
        ],
        "social awareness": [
            "How can you show kindness to someone who is feeling sad?",
            "Why is it important to say 'thank you' when someone helps you?",
            "Can you think of a way to make a new friend?"
        ],
    },
    "teen": {
        "self-awareness": [
            "What’s something you’ve accomplished recently that you’re proud of?",
            "What motivates you to keep going when things get tough?",
            "How do you usually respond to challenges?"
        ],
        "self-management": [
            "How do you handle distractions when you need to focus?",
            "What helps you stay calm when you feel overwhelmed?",
            "What’s one way you manage your time when you’re busy?"
        ],
        "social awareness": [
            "How can you support a friend who is going through a tough time?",
            "Why is it important to respect other people’s opinions?",
            "What does being a good listener mean to you?"
        ],
    },
    "adult": {
        "self-awareness": [
            "What’s one thing you’ve done recently that makes you feel accomplished?",
            "How do you usually reflect on your own emotions?",
            "What’s something you’d like to improve about yourself?"
        ],
        "self-management": [
            "How do you prioritize tasks when you’re busy?",
            "What’s a strategy you use to stay focused on long-term goals?",
            "How do you manage stress when life gets hectic?"
        ],
        "social awareness": [
            "How do you approach resolving conflicts with others?",
            "Why is empathy important in building strong relationships?",
            "What’s one way you can contribute to your community?"
        ],
    }
}

# Advanced SEL Activity Integration
SEL_CATEGORIES = {
    "self-awareness": [
        "What’s something you’re really proud of doing recently?",
        "What motivates you to be your best self?",
        "Can you share a moment when you felt truly confident?"
    ],
    "self-management": [
        "How do you stay calm when things get tough?",
        "What’s one way you manage stress effectively?",
        "How do you keep yourself focused on your goals?"
    ],
    "social awareness": [
        "What’s one kind thing someone has done for you recently?",
        "How do you show appreciation to others?",
        "Can you think of a way to support a friend in need?"
    ],
    "relationship skills": [
        "What makes a good friend?",
        "How do you resolve conflicts in a positive way?",
        "What’s one thing you can do to strengthen a relationship?"
    ],
    "decision-making": [
        "How do you decide what’s the right thing to do in a tough situation?",
        "What are the consequences of your choices, and how do you consider them?",
        "Can you think of a time you made a decision that had a positive outcome?"
    ]
}

def get_random_prompt(category):
    """
    Selects a random SEL prompt from a specified category.
    """
    return random.choice(SEL_CATEGORIES.get(category, []))

def advanced_sel_exercise(conversation_log, age):
    """
    Introduces an SEL exercise dynamically based on the user's age group.
    """
    # Determine the appropriate SEL category
    categories = list(SEL_CATEGORIES.keys())
    chosen_category = random.choice(categories)
    prompt = get_random_prompt(chosen_category)

    # Speak the prompt and capture the response
    speak(f"Let’s try a {chosen_category.replace('-', ' ')} activity. {prompt}")
    user_response = listen()

    # Process the user’s response
    if user_response:
        speak(f"Thank you for sharing your thoughts. That’s really insightful!")
        conversation_log.append({"role": "user", "content": user_response})
    else:
        speak("I didn’t catch that. Let’s move on to something else!")

# Integrate into the interaction loop
def interaction_with_advanced_sel(conversation_log, name, age):
    """
    Enhanced interaction loop that includes advanced SEL exercises.
    """
    while True:
        user_input = listen_with_dynamic_timeout(age)
        if not user_input:
            reengage_user(age)
            continue
        if is_quit_command(user_input):
            session_wrap_up(conversation_log, name, age)
            break

        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            advanced_sel_exercise(conversation_log, age)
        else:
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)

# Function to provide tailored SEL prompts
def sel_prompt_by_category(age, category):
    """
    Provides an SEL prompt based on the user's age group and selected category.
    """
    if age <= 12:
        group = "child"
    elif age <= 18:
        group = "teen"
    else:
        group = "adult"

    prompts = EXPANDED_SEL_PROMPTS.get(group, {}).get(category, [])
    if prompts:
        return random.choice(prompts)
    return None

# Function to facilitate SEL exercise
def facilitate_sel_exercise(age, category):
    """
    Guides the user through an SEL exercise based on the selected category.
    """
    prompt = sel_prompt_by_category(age, category)
    if prompt:
        speak(f"Here’s a question for you: {prompt}")
        user_response = listen()
        if user_response:
            if age <= 12:
                speak("Thank you for sharing! You’re doing such a great job.")
            elif age <= 18:
                speak("That’s really thoughtful. I appreciate you sharing that with me.")
            else:
                speak("That’s an insightful response. Thank you for reflecting on that.")
    else:
        speak("I don’t have a prompt for that category right now. Let’s talk about something else!")

# Function to handle multi-step SEL branching
def multi_step_sel_scenario(age, category):
    """
    Engages the user in a multi-step SEL scenario based on their age group.
    """
    if category == "self-awareness":
        speak("Let’s think about understanding ourselves better.")
        if age <= 12:
            speak("What’s something you’re proud of doing recently?")
            user_response = listen()
            if user_response:
                speak("Why does that make you proud?")
                listen()  # Follow-up response
                speak("That’s an amazing thing to feel proud of!")
        elif age <= 18:
            speak("Can you share a challenge you overcame recently?")
            user_response = listen()
            if user_response:
                speak("What did you learn about yourself from that experience?")
                listen()  # Follow-up response
                speak("It’s great to reflect on your personal growth.")
        else:
            speak("What’s a recent accomplishment you feel good about?")
            user_response = listen()
            if user_response:
                speak("How did achieving this impact your life?")
                listen()  # Follow-up response
                speak("That’s a meaningful achievement. Well done!")

    elif category == "social awareness":
        speak("Let’s explore how we connect with others.")
        if age <= 12:
            speak("What’s one way you can make a new friend?")
            user_response = listen()
            if user_response:
                speak("That’s a wonderful idea! Making friends is so important.")
        elif age <= 18:
            speak("How can you show support for a friend who’s feeling down?")
            user_response = listen()
            if user_response:
                speak("That’s a great way to be there for your friend.")
        else:
            speak("How do you resolve conflicts in your relationships?")
            user_response = listen()
            if user_response:
                speak("That’s a thoughtful approach to handling conflicts.")

# Function to introduce SEL activities dynamically
def dynamic_sel_activity(age):
    """
    Dynamically selects an SEL category and activity based on the user’s age.
    """
    categories = ["self-awareness", "self-management", "social awareness"]
    category = random.choice(categories)
    speak(f"Let’s do a {category.replace('-', ' ')} exercise.")
    facilitate_sel_exercise(age, category)
# ------------------------------------------------------

# Integration into main interaction logic
def interact_with_dynamic_sel(conversation_log, name, age):
    """
    Main interaction loop with SEL enhancements.
    """
    while True:
        user_input = listen_with_dynamic_timeout(age)
        if not user_input:
            reengage_user(age)
            continue
        if is_quit_command(user_input):
            session_wrap_up(conversation_log, name, age)
            break
        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            dynamic_sel_activity(age)
        else:
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)

# Additional SEL Categories and Exercises
ADDITIONAL_SEL_PROMPTS = {
    "decision-making": [
        "How do you decide what’s the right thing to do in a tough situation?",
        "What are the consequences of your choices, and how do you consider them?",
        "Can you think of a time you made a decision that had a positive outcome?"
    ],
    "relationship-building": [
        "What makes a good friend?",
        "How do you resolve conflicts in a positive way?",
        "What’s one thing you can do to strengthen a relationship?"
    ],
    "resilience": [
        "What helps you keep going when things feel hard?",
        "Can you share a time when you bounced back after a challenge?",
        "How do you stay hopeful when things don’t go as planned?"
    ]
}

# Function to provide a random SEL prompt from additional categories
def get_additional_prompt(category):
    """
    Selects a random SEL prompt from the additional categories.
    """
    return random.choice(ADDITIONAL_SEL_PROMPTS.get(category, []))

# Function for advanced SEL branching scenarios
def advanced_branching_scenario(conversation_log, age):
    """
    Presents an advanced SEL branching scenario to guide the user through reflective thinking.
    Adjusts the complexity based on age.
    """
    # Select a random category for the scenario
    categories = list(ADDITIONAL_SEL_PROMPTS.keys())
    chosen_category = random.choice(categories)
    prompt = get_additional_prompt(chosen_category)

    speak(f"Here’s a {chosen_category.replace('-', ' ')} activity: {prompt}")
    user_response = listen()
    
    if user_response:
        if age <= 12:
            speak("That’s a thoughtful response! Can you think of another way to handle this?")
        elif age <= 18:
            speak("That’s a great perspective. How would you apply this to other situations?")
        else:
            speak("Thanks for sharing your thoughts. How might this influence your future decisions?")
        conversation_log.append({"role": "user", "content": user_response})
    else:
        speak("It’s okay if you’re unsure. Let’s try another question!")

# SEL Feedback Refinement
def refine_sel_based_on_feedback(conversation_log, category, feedback_score):
    """
    Adjusts SEL category weightings based on user feedback to prioritize relevant topics.
    """
    if category not in SEL_FEEDBACK_HISTORY:
        SEL_FEEDBACK_HISTORY[category] = []

    SEL_FEEDBACK_HISTORY[category].append(feedback_score)
    average_score = sum(SEL_FEEDBACK_HISTORY[category]) / len(SEL_FEEDBACK_HISTORY[category])

    speak(f"Thank you for your feedback! I’ll remember to focus more on {category.replace('-', ' ')} activities.")

# Function for multi-step SEL exercises
def multi_step_exercise(conversation_log, age):
    """
    Guides the user through a multi-step SEL exercise that builds on their responses.
    """
    speak("Let’s try a new exercise to reflect on ourselves.")
    if age <= 12:
        scenario = "Imagine you’re a superhero. What’s your superpower, and how would you use it to help others?"
        followup = "What would you do if you lost your powers for a day?"
    elif age <= 18:
        scenario = "Think about a time you faced a challenge. What did you learn from it?"
        followup = "How would you handle a similar situation differently in the future?"
    else:
        scenario = "Describe a decision you made recently. What were the pros and cons you considered?"
        followup = "Looking back, would you change anything about how you made that decision?"

    speak(scenario)
    user_response = listen()
    if user_response:
        speak("That’s a great response! Here’s something else to consider:")
        speak(followup)
        second_response = listen()
        if second_response:
            speak("Thank you for sharing your insights. Reflection helps us grow!")
            conversation_log.append({"role": "user", "content": second_response})

# Function to integrate expanded SEL exercises into main interaction loop
def interaction_with_expanded_sel(conversation_log, name, age):
    """
    Interaction loop with expanded SEL exercises and feedback handling.
    """
    while True:
        user_input = listen_with_dynamic_timeout(age)
        if not user_input:
            reengage_user(age)
            continue

        if is_quit_command(user_input):
            session_wrap_up(conversation_log, name, age)
            break

        # Handle negative or positive emotion keywords
        if any(word in user_input for word in NEGATIVE_KEYWORDS):
            emotion_adaptive_scenario(user_input, age)
        elif any(word in user_input for word in POSITIVE_KEYWORDS):
            advanced_branching_scenario(conversation_log, age)
        else:
            # Generate a dynamic response and append feedback
            response = generate_response(user_input, conversation_log)
            update_conversation_memory(conversation_log, user_input, response)
            speak(response)

            # Add feedback after responses
            feedback_score = collect_feedback(conversation_log, response)
            refine_sel_based_on_feedback(conversation_log, "dynamic-response", feedback_score)

    # Start the Bottle server
# Start the Bottle server 
app = Bottle()

@app.post('/chat')
def chat():
    """
    Handle chat messages via API.
    """
    user_input = request.json.get('message')  # Correct usage of Bottle's request object
    if not user_input:
        response.status = 400  # Set HTTP status to 400 for bad requests
        return {"error": "No message provided"}

    try:
        # Replace with your chatbot logic
        bot_response = generate_response(user_input)  # Correctly calls your chatbot's response function
        return {"response": bot_response}  # JSON response structure
    except Exception as e:
        response.status = 500  # Set HTTP status to 500 for server errors
        return {"error": str(e)}  # Return error details for debugging

if __name__ == "__main__":
    # Start the Bottle server
    run(app, host="localhost", port=5000, debug=True)  # Debug mode enabled for detailed error messages






