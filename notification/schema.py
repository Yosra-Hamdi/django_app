import graphene
from graphene_django.types import DjangoObjectType
from .models import Notification
from orders.models import Order

# Type GraphQL pour Notification
class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification

# Query pour récupérer toutes les notifications
class Query(graphene.ObjectType):
    all_notifications = graphene.List(NotificationType, is_read=graphene.Boolean())

    def resolve_all_notifications(self, info, is_read=None):
        queryset = Notification.objects.all().order_by('-created_at')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        return queryset

# Mutation pour créer une notification
class CreateNotification(graphene.Mutation):
    class Arguments:
        title = graphene.String(required=True)
        body = graphene.String(required=True)
        order_id = graphene.ID(required=False)

    notification = graphene.Field(NotificationType)

    def mutate(self, info, title, body, order_id=None):
        order = Order.objects.get(id=order_id) if order_id else None
        notification = Notification.objects.create(
            title=title,
            body=body,
            order=order
        )
        return CreateNotification(notification=notification)

# Mutation pour marquer une notification comme lue
class MarkNotificationAsRead(graphene.Mutation):
    class Arguments:
        notification_id = graphene.ID(required=True)

    success = graphene.Boolean()

    def mutate(self, info, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return MarkNotificationAsRead(success=True)
        except Notification.DoesNotExist:
            return MarkNotificationAsRead(success=False)

# Schéma GraphQL avec Query et Mutations
class Mutation(graphene.ObjectType):
    create_notification = CreateNotification.Field()
    mark_notification_as_read = MarkNotificationAsRead.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
