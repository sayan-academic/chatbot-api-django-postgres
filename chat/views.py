import os
from django.shortcuts import render, redirect
from django.http import JsonResponse
from google import genai  # Note the new import
from dotenv import load_dotenv
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomRegistrationForm, CustomLoginForm

from chat.models import ChatMessage

load_dotenv()

# New 2026 Client initialization
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def register_view(request):
    if request.method == 'POST':
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save() # This triggers the INSERT INTO auth_user Postgres command!
            login(request, user)
            return redirect('chat:chat_home')
    else:
        form = CustomRegistrationForm()
    return render(request, 'chatbot/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('chat:chat_home')
    else:
        form = CustomLoginForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        session_key = request.session.session_key
        if session_key:
            ChatMessage.objects.filter(session_key=session_key).delete()
        logout(request)
        return redirect('chat:login')

@login_required(login_url='chat:login')
def chat_home(request):

    if not request.session.session_key:
            request.session.create()

    current_session_key = request.session.session_key

    if request.method == "POST":

        user_text = request.POST.get('message')
        
        # 1. FETCH RECENT HISTORY FROM POSTGRES
        # We grab the last 10 messages to provide context without overloading tokens
        db_messages = list(ChatMessage.objects.filter(
            user=request.user, 
            session_key=current_session_key
        ).order_by('-created_at')[:10])

        ChatMessage.objects.create(
            user=request.user, 
            session_key=current_session_key, 
            role='user', 
            content=user_text
        )
        # 2. FORMAT FOR GEMINI (The SDK expects a specific list structure)
        # We reverse because we fetched the 'latest' first, but Gemini needs chronological order
        history = []
        for msg in reversed(db_messages):
            history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}]
            })

        # 3. CHAT LOGIC WITH FALLBACK
        try:
            # Primary attempt
            chat = client.chats.create(
                model='gemini-3.1-flash-lite-preview',
                history=history
            )
            response = chat.send_message(user_text)
            ai_response = response.text
            source = ""

        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print("Switching to backup model...")
                try:
                    chat = client.chats.create(
                        model='gemini-2.5-flash',
                        history=history
                    )
                    response = chat.send_message(user_text)
                    ai_response = response.text
                    source = "(Backup) "
                except Exception:
                    return JsonResponse({'response': "All models busy."}, status=503)
            else:
                return JsonResponse({'response': f"System Error: {str(e)}"}, status=500)

        # 4. SAVE TO POSTGRESQL
        # This replaces the session.append logic
        ChatMessage.objects.create(
            user=request.user, 
            session_key=current_session_key, 
            role='model', 
            content=ai_response # Replace with whatever variable holds your Gemini output
        )

        return JsonResponse({'response': f"{source}{ai_response}"})

    # 5. INITIAL PAGE LOAD
    # Fetch all history so the user sees their past chats when they open the page
    full_history = ChatMessage.objects.filter(
        user=request.user, 
        session_key=current_session_key
    ).order_by('created_at')
    return render(request, 'chatbot/homepage.html', {'history': full_history})