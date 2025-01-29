from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from requests import get
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.request import Request
from rest_framework.response import Response
from yaml import load as load_yaml, Loader
from django.db.models import Q

from backend.models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter, ConfirmEmailToken, Contact
from backend.serializers import UserSerializer, ContactSerializer
from backend.signals import new_user_registered

from django.contrib.auth.models import update_last_login


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """

    # Регистрация методом POST
    def post(self, request, *args, **kwargs):
        """
            Обработка POST запроса и создание нового пользователя.

            Args:
                request (Request): Объект Django запроса.

            Returns:
                JsonResponse: Ответ с указанием статуса операции и любых ошибок.
            """
        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):

            # проверяем пароль на сложность
            sad = 'asd'
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                # проверяем данные для уникальности имени пользователя

                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """

    # Регистрация методом POST
    def post(self, request, *args, **kwargs):
        """
            Подтверждает почтовый адрес пользователя.

            Args:
            - request (Request): Объект Django запроса.

            Returns:
            - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
            """
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class AccountDetails(APIView):
    """
    Класс для управления данными учетной записи пользователя.

    Методы:
    - get: Получение данных о прошедшем проверку подлинности пользователе.
    - post: Обновление данных аккаунта прошедшего проверку подлинности пользователя.

    Attributes:
    - None
    """

    # получить данные
    def get(self, request: Request, *args, **kwargs):
        """
           Получение данных о прошедшем проверку подлинности пользователе.

           Args:
           - request (Request): Объект Django запроса.

           Returns:
           - Response: Ответ, содержащий сведения о прошедшем проверку подлинности пользователе.
            """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Необходимо авторизоваться в системе'}, status=403)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Редактирование методом POST
    def post(self, request, *args, **kwargs):
        """
            Обновление данных аккаунта прошедшего проверку подлинности пользователя.

            Args:
            - request (Request): Объект Django запроса.

            Returns:
            - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
            """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Необходимо авторизоваться в системе'}, status=403)
        # проверяем обязательные аргументы

        if 'password' in request.data:
            errors = {}
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})
            else:
                request.user.set_password(request.data['password'])

        # проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return JsonResponse({'Status': True})
        else:
            return JsonResponse({'Status': False, 'Errors': user_serializer.errors})


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """

    # Авторизация методом POST
    def post(self, request, *args, **kwargs):
        """
            Авторизация пользователя.

            Args:
                request (Request): Объект Django запроса.

            Returns:
                JsonResponse: Ответ с указанием статуса операции и любых ошибок.
            """
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])
            print(f'{type(user)} {user}')
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    update_last_login(None, token.user) # Для обновления last_login через API
                    return JsonResponse({'Status': True, 'Token': token.key})

            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ContactView(APIView):
    """
       Класс для управления контактной информацией.

       Методы:
       - get: Получение контактной информации о прошедшем проверку подлинности пользователе.
       - post: Создание новой контактной информации о прошедшем проверку подлинности пользователе.
       - put: Обновление контактной информации о прошедшем проверку подлинности пользователе.
       - delete: Удаление контактной информации о прошедшем проверку подлинности пользователе.

       Attributes:
       - None
       """

    # получить мои контакты
    def get(self, request, *args, **kwargs):
        """
           Получение контактной информации о прошедшем проверку подлинности пользователе.

           Args:
           - request (Request): Объект Django запроса.

           Returns:
           - Response: Ответ с указанием контактной информации и любых ошибок.
           """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Не удалось авторизовать пользователя'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # добавить новый контакт с типом тела запроса form-data
    def post(self, request, *args, **kwargs):
        """
            Создание новой контактной информации о прошедшем проверку подлинности пользователе.

            Args:
            - request (Request): Объект Django запроса.

            Returns:
            - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
            """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'city', 'street', 'phone'}.issubset(request.data):
            print(type(request.data))
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                return JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # добавить новый контакт с типом тела запроса raw
    # def post(self, request, *args, **kwargs):
    #     """
    #        Создание новой контактной информации о прошедшем проверку подлинности пользователе.
    #
    #        Args:
    #        - request (Request): Объект Django запроса.
    #
    #        Returns:
    #        - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
    #        """
    #     if not request.user.is_authenticated:
    #         return JsonResponse({'Status': False, 'Error': 'Не удалось авторизовать пользователя'}, status=403)
    #     print(request.data)
    #     if {'city', 'street', 'phone'}.issubset(request.data):
    #         # request.data._mutable = True
    #         request.data.update({'user': request.user.id})
    #         serializer = ContactSerializer(data=request.data)
    #
    #         if serializer.is_valid():
    #             serializer.save()
    #             return JsonResponse({'Status': True})
    #         else:
    #             return JsonResponse({'Status': False, 'Errors': serializer.errors})
    #
    #     return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


    # редактировать контакт
    def put(self, request, *args, **kwargs):
        """
           Обновление контактной информации о прошедшем проверку подлинности пользователе.

           Args:
           - request (Request): Объект Django запроса.

           Returns:
           - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
           """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Не удалось авторизовать пользователя'}, status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                print(contact)
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})
                else:
                    return JsonResponse({'Status': False, 'Errors': 'Контакт с указанным ID не найден'})

        return JsonResponse({'Status': False, 'Errors': 'Не указан ID контакта для изменения'})

    # удалить контакт
    def delete(self, request, *args, **kwargs):
        """
           Удаление контактной информации о прошедшем проверку подлинности пользователе.

           Args:
           - request (Request): Объект Django запроса.

           Returns:
           - JsonResponse: Ответ с указанием статуса операции и любых ошибок.
           """
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Не удалось авторизовать пользователя'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Требуется авторизация'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})