from django.shortcuts import render,redirect
from .models import Book, Genres, User_Book_Reading, User_Book_Wishlisted, User_Book_Currently_Reading, Intermediate_Book
from .forms import NewUserForm

from django.core.paginator import Paginator

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

import numpy as np
import pandas as pd

import tensorflow as tf
import tensorflow.keras as keras
from tensorflow.keras import Model
from tensorflow.keras.models import model_from_json
from tensorflow.keras import backend as K

import json

genres = ['Fiction', 'Fantasy', 'Romance', 'Young Adult', 'Historical', 'Paranormal', 'Mystery', 'Nonfiction', 'Science Fiction', 
'Historical Fiction', 'Classics', 'Contemporary', 'Childrens', 'Cultural', 'Literature', 'Sequential Art', 'Thriller', 'European Literature', 
'Religion', 'History', 'Biography', 'Humor', 'Horror', 'Novels', 'Adventure', 'Crime', 'Contemporary Romance', 'Autobiography', 'Philosophy', 
'War', 'Short Stories', 'Christian', 'Paranormal Romance', 'Vampires', 'Comics', 'Womens Fiction', 'Memoir', 'Chick Lit', 'Erotica', 'Science']


dataset = pd.read_csv('scripts/goodbooks-10k-master/ratings.csv')
book_data = np.array(list(set(dataset.book_id)))
books_csv = pd.read_csv('scripts/goodbooks-10k-master/books.csv')


class Home:
    def home(request):
        print ("**************Going to the Home Page**************")
        return render(request, 'books/home.html', {})

class Search:
    def search_books(request):
        return render(request, 'books/search.html', {})

    def search(request):
        query = request.GET.get('search_value')
        book_list = Book.objects.filter(title__contains=query)
        genres = Genres.objects.all()

        page = request.GET.get('page', 1)

        paginator = Paginator(book_list, 1000)
        try:
            books = paginator.page(page)
        except PageNotAnInteger:
            books = paginator.page(1)
        except EmptyPage:
            books = paginator.page(paginator.num_pages)

        return render(request, 'books/all_books.html', {'books':books,'genres':genres,'focus_genre':"False",'search_header':f"Search Results For: {query}"})

class Find_Books:
    def all_books(request):
        book_list = Book.objects.all()
        genres = Genres.objects.all()
        
        page = request.GET.get('page', 1)

        paginator = Paginator(book_list, 1000)
        try:
            books = paginator.page(page)
        except PageNotAnInteger:
            books = paginator.page(1)
        except EmptyPage:
            books = paginator.page(paginator.num_pages)

        return render(request, 'books/all_books.html', {'books':books,'genres':genres,'focus_genre':"False" })

    def sort_books_genre(request,request_genre):
        if request_genre in genres:
            book_list = Book.objects.filter(genres__contains=request_genre)
            genre = Genres.objects.all()

            page = request.GET.get('page', 1)

            paginator = Paginator(book_list, 1000)
            try:
                books = paginator.page(page)
            except PageNotAnInteger:
                books = paginator.page(1)
            except EmptyPage:
                books = paginator.page(paginator.num_pages)

            return render(request, 'books/all_books.html', {'books':books,'genres':genre,'focus_genre':request_genre})
        else:
            return redirect('all_books')

class Book_Functions:
    def about_book(request,pk,status='',current_page=''):
        book = Book.objects.get(pk=pk)
        return render(request, 'books/about_books.html', {'book':book,'status':status,'current_page':current_page})


    def add_to_wishlist(request,pk,status=False):
        try:
            book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
        except Exception as e:
            print (str(e))
            book1 = Book.objects.get(pk=pk)
            book = Intermediate_Book(user = request.user,book=book1,current_page = 0,status = "To Read")

        book.status = "To Read"
        book.current_page = 0
        book.save()

        output = User_Book_Wishlisted.objects.get(user__pk=request.user.pk)
        output.book.add(book)
        output.save()

        try:
            output_currently_reading = User_Book_Currently_Reading.objects.get(user__pk=request.user.pk)
            output_currently_reading.book.remove(book)
            output_currently_reading.save()
        except Exception as e:
            print (str(e))
        try:
            output_reading = User_Book_Reading.objects.get(user__pk=request.user.pk)
            output_reading.book.remove(book)
            output_reading.save()
        except Exception as e:
            print (str(e))
        return redirect('about_book', pk=pk,status = book.status,current_page = book.current_page)

    def remove_from_wishlist(request,pk,status=False):
        book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
        book.delete()
        
        return redirect('about_book', pk=pk,status = "Not Read",current_page = 0)


    def currently_reading(request,pk,status=False):
        try:
            book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
        except:

            book1 = Book.objects.get(pk=pk)
            book = Intermediate_Book(user = request.user,book=book1,current_page = 0,status = "Reading")
        book.status = "Reading"
        book.current_page = 0
        book.save()
        print (book)
        output = User_Book_Currently_Reading.objects.get(user__pk=request.user.pk)
        output.book.add(book)
        try:
            output = User_Book_Wishlisted.objects.get(user__pk=request.user.pk)
            output.book.remove(book)
        except Exception as e:
            print (str(e))
        try:
            output = User_Book_Reading.objects.get(user__pk=request.user.pk)
            output.book.remove(book)
        except Exception as e:
            print (str(e))
        return redirect('about_book', pk=pk,status = book.status,current_page = book.current_page)

    def remove_currently_reading(request,pk,status=False):
        book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
        book.delete()
        return redirect('about_book', pk=pk,status = "Not Read",current_page = 0)

    def change_current_page(request,pk,status="In Progress"):
        if status=="In Progress":
            obj = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
            book = Book.objects.get(pk=pk)
            return render(request, 'books/about_books.html', {'book':book,'flag':"In Progress",'status':obj.status,'current_page':obj.current_page})
        else:
            book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
            book.current_page = request.GET.get('new_page')
            book.save()
            return redirect('about_book', pk=pk,status = book.status,current_page = book.current_page)

    def already_read_book(request,pk,status=False):
        try:
            book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
        except:

            book1 = Book.objects.get(pk=pk)
            book = Intermediate_Book(user = request.user,book=book1,current_page = 0,status = "Reading")
        book.status = "Read"
        book.current_page = 0
        book.save()
        print (book)
        output = User_Book_Reading.objects.get(user__pk=request.user.pk)
        output.book.add(book)
        try:
            output = User_Book_Wishlisted.objects.get(user__pk=request.user.pk)
            output.book.remove(book)
        except Exception as e:
            print (str(e))
        try:
            output = User_Book_Currently_Reading.objects.get(user__pk=request.user.pk)
            output.book.remove(book)
        except Exception as e:
            print (str(e))
        return redirect('about_book', pk=pk,status = book.status,current_page = book.current_page)



class Services:
    def services(request):
        return render(request, 'books/services.html', {})

class Registration:
    def register(request):
        if request.method == "POST":
            form = UserCreationForm(request.POST)
            if form.is_valid():
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f"New account created: {username}")
                user_data_1 = User_Book_Reading(user=user)
                user_data_1.save()
                user_data_2 = User_Book_Wishlisted(user=user)
                user_data_2.save()
                user_data_3 = User_Book_Currently_Reading(user=user)
                user_data_3.save()
                login(request, user)
                
                return redirect("home")

            else:
                for msg in form.error_messages:
                    messages.error(request, f"{msg}: {form.error_messages[msg]}")

                return render(request = request,
                              template_name = "registration/signup.html",
                              context={"form":form})

        form = UserCreationForm
        return render(request = request,
                      template_name = "registration/signup.html",
                      context={"form":form})

    def login_request(request):
        if request.method == 'POST':
            form = AuthenticationForm(request=request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.info(request, f"You are now logged in as {username}")
                    return redirect('home')
                else:
                    messages.error(request, "Invalid username or password.")
            else:
                messages.error(request, "Invalid username or password.")
        form = AuthenticationForm()
        return render(request = request,
                        template_name = "registration/login.html",
                        context={"form":form})
    def logout_request(request):
        logout(request)
        messages.info(request, "Logged out successfully!")
        return redirect("home")



class User_Book_Data:

    def view_user_data(request,user_data_link):

        if user_data_link=="Read":
            output = User_Book_Reading.objects.get(user__pk=request.user.pk)
        elif user_data_link=="Wishlist":
            output = User_Book_Wishlisted.objects.get(user__pk=request.user.pk)
        elif user_data_link=="Reading":
            output = User_Book_Currently_Reading.objects.get(user__pk=request.user.pk)
            
        queryset = output.book.all()
        books = Book.objects.filter(goodreads_book_id__in = [e.book.goodreads_book_id for e in queryset])
        return render(request, 'books/user_books.html', {'books':books})

    def redirect_clicked_book(request,pk):
        if request.user.is_authenticated:
            try:
                book = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=pk)
            except:
                obj = Book.objects.get(pk=pk)
                book = Intermediate_Book(user = request.user,book=obj,current_page = 0,status = "Not Read")
            return redirect('about_book', pk=pk,status = book.status,current_page = book.current_page)
        else:
            obj = Book.objects.get(pk=pk)
            return redirect('about_book', pk=pk,status = "Not Read",current_page = 0)



    @csrf_exempt
    def handle_selected_books(request):
        selected_books = request.POST.getlist("selected[]")
        print(selected_books)

        output = User_Book_Reading.objects.get(user__pk=request.user.pk)
        for id_obj in selected_books:
            try:
                book_obj = Intermediate_Book.objects.get(user__pk=request.user.pk,book__pk=id_obj)
            except:
                book1 = Book.objects.get(pk=id_obj)
                book_obj = Intermediate_Book(user = request.user,book=book1,current_page = 0,status = "Read")
                book_obj.save()
            output.book.add(book_obj)
            output.save()

            try:
                output_currently_reading = User_Book_Currently_Reading.objects.get(user__pk=request.user.pk)
                output_currently_reading.book.remove(book_obj)
                output_currently_reading.save()
            except Exception as e:
                print (str(e))
            try:
                output_reading = User_Book_Wishlisted.objects.get(user__pk=request.user.pk)
                output_reading.book.remove(book_obj)
                output_reading.save()
            except Exception as e:
                print (str(e))

        return HttpResponse("Success")
        #return HttpResponse('Success')
    def select_read_books(request):
        books = Book.objects.all()[:500]
        return render(request, 'books/select_read_books.html', {'books':books})

class Recommend_Books:

    def predictions(request):

        tf.keras.backend.clear_session()

        json_file = open('scripts/model.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()

        loaded_model = model_from_json(loaded_model_json)
        loaded_model.load_weights("scripts/model.h5")
        print("Loaded model from disk")
        loaded_model.compile('adam', 'mean_squared_error')

        #get user_data
        #user_data = np.array([1 for i in range(10000)])
        user_data = np.array([0 for i in range(10000)])
        output = User_Book_Reading.objects.get(user__pk=request.user.pk)
        queryset = output.book.all()
        for query in queryset:
            id_of_book = query.book.book_id
            user_data[int(id_of_book)-1] = 1



        user = np.array(user_data) #[1,1,0,1,0,0,0......0,1,1]
        predictions = loaded_model.predict([user, book_data])
        predictions = np.array([a[0] for a in predictions])
        recommended_book_ids = (-predictions).argsort()[:100]

        output = books_csv[books_csv['book_id'].isin(recommended_book_ids)]

        K.clear_session()

        books = Book.objects.filter(goodreads_book_id__in = list(output.goodreads_book_id))


        return render(request, 'books/all_books.html', {'books':books,'search_header':"Your Recommendations"})

