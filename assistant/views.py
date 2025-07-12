from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import AdminRegisterForm, AdminLoginForm, ProductForm
from .models import Product
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def chat_view(request):
    return render(request, "chat.html")
for m in genai.list_models():
    print(m.name, "supports", m.supported_generation_methods)


# Function to format product info for the chatbot prompt
def format_product_data():
    products = Product.objects.all()
    if not products:
        return "Currently, there are no products available."
    return "\n".join([
        f"{p.name} - ₹{p.price}, Location: {p.location}" for p in products
    ])

def generate_gpt_reply(user_input):
    product_info = format_product_data()

    prompt = f"""
You are a helpful and creative store assistant. Only respond with details relevant to the user's question.

Don't list all products by default.

Here is internal product data for you to use if needed:
{product_info}

Instructions for replies:
- Respond warmly and concisely.
- Use short lines and bullet points using * or dashes.
- Suggest products based on the user's interest.
- Do NOT show all available products unless asked.
- After each suggestion give some facts about the suggestion and ask if the customer needs something else.

User: {user_input}
Assistant:
"""

    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        response = model.generate_content(prompt)

        # Clean formatting for HTML display
        formatted = (
            response.text.replace('\n', '<br>')
                         .replace('*', '•')
                         .replace('- ', '• ')
        )
        return formatted
    except Exception as e:
        return f"Oops! I had a glitch trying to answer that 😅 ({str(e)})"


def get_response(request):
    user_input = request.GET.get('msg', '').lower()
    reply = generate_gpt_reply(user_input)
    return JsonResponse({"reply": reply})

def admin_register(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.is_staff = True
            user.save()
            return redirect('admin_login')
    else:
        form = AdminRegisterForm()
    return render(request, 'admin_register.html', {'form': form})

def admin_login(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['password'])
            if user is not None and user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
    else:
        form = AdminLoginForm()
    return render(request, 'admin_login.html', {'form': form})

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('admin_login')

    form = ProductForm()
    products = Product.objects.all()

    if request.method == 'POST':
        if 'add' in request.POST:
            form = ProductForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('admin_dashboard')
        elif 'edit_id' in request.POST:
            product = get_object_or_404(Product, id=request.POST.get('edit_id'))
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                form.save()
                return redirect('admin_dashboard')

    return render(request, 'admin_dashboard.html', {'form': form, 'products': products})

@login_required
def delete_product(request, product_id):
    if request.user.is_staff:
        product = get_object_or_404(Product, id=product_id)
        product.delete()
    return redirect('admin_dashboard')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')
@login_required
def store_map(request):
    products = Product.objects.all()
    return render(request, 'store_map.html', {'products': products})
