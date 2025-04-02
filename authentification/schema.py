import graphene
from graphql_jwt.shortcuts import get_token
import random
from django.core.mail import send_mail
from django.conf import settings
from graphene import relay
from graphene_django import DjangoObjectType
import graphql_jwt
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from graphql import GraphQLError

from authentification.models import User
from .utils import send_password_reset_email  # Importez la fonction utilitaire

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        interfaces = (relay.Node,)
        fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'store_name')

class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    message = graphene.String()
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        phone = graphene.String(required=True)
        store_name = graphene.String(required=True)
        username = graphene.String(required=False)

    def mutate(self, info, first_name, last_name, email, password, phone, store_name ,username=None):

        user = get_user_model()
         # Générer un username unique si non fourni
        if not username:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
        if User.objects.filter(email=email).exists():
            raise Exception("Cet e-mail est déjà utilisé. Veuillez en choisir un autre.")


        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,  # Ajouter un username unique
            phone=phone,
            store_name=store_name,
        )
        user.set_password(password)
        user.save()
        return CreateUser(user=user , message="Compte créé avec succès !")



class RequestPasswordReset(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError('Aucun utilisateur trouvé avec cet e-mail')

        # Générer un code aléatoire (par exemple, 4 chiffres)
        reset_code = str(random.randint(1000, 9999))

        # Stocker le code dans le modèle utilisateur (ou en mémoire)
        user.reset_code = reset_code
        user.save()

        # Envoyer l'e-mail avec le code
        subject = 'Réinitialisation de votre mot de passe'
        message = f'''
        Bonjour,

        Nous vous avons envoyé cet e-mail en réponse à votre demande de réinitialisation de votre mot de passe.

        Votre code de réinitialisation est : {reset_code}

        Veuillez ignorer cet e-mail si vous n’avez pas demandé de changement de mot de passe.
        '''
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Expéditeur
                [user.email],  # Destinataire
                fail_silently=False,
            )
        except Exception as e:
            raise GraphQLError(f"Erreur lors de l'envoi de l'email : {str(e)}")

        return RequestPasswordReset(success=True)
    



class ResetPassword(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)  # Code de réinitialisation
        new_password = graphene.String(required=True)

    def mutate(self, info, email, code, new_password):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError('Utilisateur introuvable')

        # Vérifier le code de réinitialisation
        if user.reset_code != code:
            raise GraphQLError('Code de réinitialisation invalide')

        # Réinitialiser le mot de passe
        user.set_password(new_password)
        user.reset_code = None  # Effacer le code après utilisation
        user.save()

        return ResetPassword(success=True)
    
class ResendResetCode(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)

    def mutate(self, info, email):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError('Aucun utilisateur trouvé avec cet e-mail')

        # Générer un nouveau code aléatoire (4 chiffres)
        new_reset_code = str(random.randint(1000, 9999))

        # Mettre à jour le code dans le modèle utilisateur
        user.reset_code = new_reset_code
        user.save()

        # Envoyer l'e-mail avec le nouveau code
        subject = 'Réinitialisation de votre mot de passe'
        message = f'''
        Bonjour,

        Nous vous avons envoyé cet e-mail en réponse à votre demande de réinitialisation de votre mot de passe.

        Votre nouveau code de réinitialisation est : {new_reset_code}

        Veuillez ignorer cet e-mail si vous n’avez pas demandé de changement de mot de passe.
        '''
        try:
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Expéditeur
                [user.email],  # Destinataire
                fail_silently=False,
            )
        except Exception as e:
            raise GraphQLError(f"Erreur lors de l'envoi de l'email : {str(e)}")

        return ResendResetCode(success=True)



class Query(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user_by_id = graphene.Field(UserType, id=graphene.Int(required=True))
    user_by_email = graphene.Field(UserType, email=graphene.String(required=True))

    def resolve_all_users(self, info):
        return get_user_model().objects.all()

    def resolve_user_by_id(self, info, id):
        try:
            return get_user_model().objects.get(id=id)
        except get_user_model().DoesNotExist:
            raise GraphQLError('User not found')

    def resolve_user_by_email(self, info, email):
        try:
            return get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise GraphQLError('User not found')

class LoginUser(graphene.Mutation):
    token = graphene.String()
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError("Utilisateur introuvable")

        if not user.check_password(password):
            raise GraphQLError("Mot de passe incorrect")

        token = get_token(user)


        return LoginUser(token=token, user=user)
    

class VerifyResetCode(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)
        code = graphene.String(required=True)

    def mutate(self, info, email, code):
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise GraphQLError('Aucun utilisateur trouvé avec cet e-mail')

        # Vérifier si le code saisi correspond au code stocké
        if user.reset_code != code:
            raise GraphQLError('Code de réinitialisation invalide')

        return VerifyResetCode(success=True)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    login = LoginUser.Field()  
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    request_password_reset = RequestPasswordReset.Field()
    reset_password = ResetPassword.Field()
    resend_reset_code = ResendResetCode.Field()
    verify_reset_code = VerifyResetCode.Field()  
 


schema = graphene.Schema(query=Query, mutation=Mutation)