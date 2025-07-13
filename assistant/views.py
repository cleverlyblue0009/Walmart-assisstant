from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import AdminRegisterForm, AdminLoginForm, ProductForm
from .models import Product
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv
from django.core.files.storage import default_storage

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def chat_view(request):
    return render(request, "chat.html")

# Function to format product info for the chatbot prompt
def format_product_data():
    products = Product.objects.all()
    if not products:
        return "Currently, there are no products available."
    return "\n".join([
        f"{p.name} - ₹{p.price}, Location: {p.location}" for p in products
    ])

def generate_gpt_reply(user_input=None, detected_label=None):
    product_info = format_product_data()

    if detected_label:
        matching_product = Product.objects.filter(name__icontains=detected_label).first()
        if matching_product:
            product_fact = f"We have {matching_product.name} for ₹{matching_product.price} in {matching_product.location}."
        else:
            product_fact = f"We don't currently stock {detected_label}, but it's a wonderful choice!"

        prompt = f"""
A customer uploaded a photo.
It was detected as: "{detected_label}".

Details:
{product_fact}

Instructions:
- Respond in a short, warm tone.
- If it's in our store, mention name, price, and location nicely.
- If not, share a fun or helpful fact about the product.
- Always ask if the customer needs anything else.
"""
    else:
        prompt = f"""
You are a helpful and creative store assistant.

Here is internal product data for you to use if needed:
{product_info}

Instructions for replies:
- Greet the customer if it's a greeting like "hi" or "hello".
- Respond warmly and concisely.
- Use short lines and bullet points using * or dashes.
- Suggest products based on the user's interest.
- Do not list all products unless explicitly asked.
- If a product is not available, still give helpful information.
- Always ask if the customer needs anything else.

User: {user_input}
Assistant:
"""

    try:
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        response = model.generate_content(prompt)
        formatted = "<br>".join([
            line.strip() for line in response.text.replace('*', '•').replace('- ', '• ').split('\n') if line.strip()
        ])
        return formatted
    except Exception as e:
        return f"Oops! I had a glitch trying to answer that 😅 ({str(e)})"

def get_response(request):
    user_input = request.GET.get('msg', '').lower()
    reply = generate_gpt_reply(user_input=user_input)
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
    categories = Product.objects.values_list('category', flat=True).distinct()

    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def view_category(request, category_name):
    if not request.user.is_staff:
        return redirect('admin_login')

    products = Product.objects.filter(category=category_name)
    return render(request, 'category_view.html', {'category': category_name, 'products': products})

@login_required
def add_or_edit_product(request):
    if not request.user.is_staff:
        return redirect('admin_login')

    form = ProductForm()
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

    return render(request, 'admin_dashboard.html', {'form': form})

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

@csrf_exempt
@login_required
def analyze_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        img_file = request.FILES['image']
        file_path = default_storage.save('uploads/' + img_file.name, img_file)

        try:
            image = Image.open(default_storage.path(file_path)).convert("RGB")
            model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
            response = model.generate_content(["What is in this image? Give only the name of the object.", image])
            label = response.text.strip().split('\n')[0]
        except Exception as e:
            return JsonResponse({"reply": f"Gemini image analysis failed: {str(e)}"}, status=500)

        reply = generate_gpt_reply(detected_label=label)
        return JsonResponse({"reply": reply})

    return JsonResponse({"reply": "No image provided."}, status=400)
