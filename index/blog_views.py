"""
Blog API views for the Leisuretimez platform.

Handles blog posts (CRUD), comments, and reactions.
Admin/staff can create, update, and delete posts.
Authenticated users can comment and react.
Anyone can read published posts.
"""

import logging

from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BlogComment, BlogPost, BlogReaction, CustomUser
from .serializers import (
    BlogCommentCreateSerializer, BlogCommentSerializer,
    BlogPostCreateSerializer, BlogPostSerializer,
    BlogReactSerializer, BlogReactionSerializer,
)
from .utils import create_notification

logger = logging.getLogger(__name__)


def _unique_slug(title, instance=None):
    """Generate a unique slug from the title."""
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    qs = BlogPost.objects.all()
    if instance:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _notify_new_blog_post(post):
    """Send notification to all active users about a new blog post."""
    users = CustomUser.objects.filter(is_active=True).exclude(pk=post.author.pk)
    notifications = []
    for user in users.iterator():
        notifications.append(
            create_notification(
                user=user,
                notification_type='new_blog_post',
                title='New Blog Post',
                message=f'New post: "{post.title}" — {post.excerpt[:100] if post.excerpt else post.content[:100]}...',
            )
        )
    logger.info("Notified %d users about new blog post '%s'", len(notifications), post.title)


def _notify_blog_comment(comment):
    """Notify the post author when someone comments on their post."""
    post = comment.post
    if comment.user == post.author:
        return
    create_notification(
        user=post.author,
        notification_type='blog_comment',
        title='New Comment on Your Post',
        message=f'{comment.user.firstname} {comment.user.lastname} commented on "{post.title}": "{comment.content[:80]}..."',
    )


def _notify_blog_reaction(reaction):
    """Notify the post author when someone reacts to their post."""
    post = reaction.post
    if reaction.user == post.author:
        return
    create_notification(
        user=post.author,
        notification_type='blog_reaction',
        title='New Reaction on Your Post',
        message=f'{reaction.user.firstname} {reaction.user.lastname} {reaction.reaction_type}d your post "{post.title}".',
    )


# ---------------------------------------------------------------------------
# Blog Post ViewSet
# ---------------------------------------------------------------------------

class BlogPostViewSet(viewsets.ModelViewSet):
    """CRUD for blog posts.

    - List/Retrieve: anyone (published posts only for non-staff)
    - Create/Update/Delete: staff/admin only
    """

    serializer_class = BlogPostSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return BlogPost.objects.all()
        return BlogPost.objects.filter(status='published')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        serializer = BlogPostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post_status = serializer.validated_data.get('status', 'draft')
        published_at = timezone.now() if post_status == 'published' else None

        post = BlogPost.objects.create(
            author=request.user,
            title=serializer.validated_data['title'],
            slug=_unique_slug(serializer.validated_data['title']),
            content=serializer.validated_data['content'],
            excerpt=serializer.validated_data.get('excerpt', ''),
            cover_image=serializer.validated_data.get('cover_image'),
            status=post_status,
            tags=serializer.validated_data.get('tags', ''),
            published_at=published_at,
        )

        if post_status == 'published':
            _notify_new_blog_post(post)

        return Response(
            BlogPostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        serializer = BlogPostCreateSerializer(data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)

        was_draft = post.status != 'published'

        if 'title' in serializer.validated_data:
            post.title = serializer.validated_data['title']
            post.slug = _unique_slug(post.title, instance=post)
        if 'content' in serializer.validated_data:
            post.content = serializer.validated_data['content']
        if 'excerpt' in serializer.validated_data:
            post.excerpt = serializer.validated_data['excerpt']
        if 'cover_image' in serializer.validated_data:
            post.cover_image = serializer.validated_data['cover_image']
        if 'tags' in serializer.validated_data:
            post.tags = serializer.validated_data['tags']
        if 'status' in serializer.validated_data:
            post.status = serializer.validated_data['status']

        # Set published_at when first published
        if was_draft and post.status == 'published' and not post.published_at:
            post.published_at = timezone.now()
            _notify_new_blog_post(post)

        post.save()

        return Response(
            BlogPostSerializer(post, context={'request': request}).data,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # --- Extra actions ---

    @action(detail=True, methods=['get'])
    def reactions(self, request, slug=None):
        """List reactions for a post with summary."""
        post = self.get_object()
        summary = dict(
            post.reactions.values_list('reaction_type')
            .annotate(count=Count('id'))
            .values_list('reaction_type', 'count')
        )
        return Response({
            'total': post.reactions.count(),
            'summary': summary,
            'reactions': BlogReactionSerializer(post.reactions.all(), many=True).data,
        })


# ---------------------------------------------------------------------------
# Blog Comment Views
# ---------------------------------------------------------------------------

@api_view(['GET', 'POST'])
def blog_comment_create(request, slug):
    """List comments (GET, public) or add a comment (POST, auth required)."""
    try:
        post = BlogPost.objects.get(slug=slug, status='published')
    except BlogPost.DoesNotExist:
        return Response(
            {'error': 'Blog post not found'}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        comments = post.comments.filter(parent__isnull=True)
        return Response(BlogCommentSerializer(comments, many=True).data)

    # POST — authentication required
    if not request.user.is_authenticated:
        return Response(
            {'detail': 'Authentication credentials were not provided.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = BlogCommentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    parent = serializer.validated_data.get('parent')
    if parent and parent.post != post:
        return Response(
            {'error': 'Parent comment does not belong to this post'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    comment = BlogComment.objects.create(
        post=post,
        user=request.user,
        parent=parent,
        content=serializer.validated_data['content'],
    )

    _notify_blog_comment(comment)

    return Response(
        BlogCommentSerializer(comment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def blog_comment_detail(request, comment_id):
    """Update or delete the user's own comment."""
    try:
        comment = BlogComment.objects.get(id=comment_id, user=request.user)
    except BlogComment.DoesNotExist:
        return Response(
            {'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'DELETE':
        comment.delete()
        return Response({'status': 'success', 'message': 'Comment deleted'})

    serializer = BlogCommentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    comment.content = serializer.validated_data['content']
    comment.save()
    return Response(BlogCommentSerializer(comment).data)


# ---------------------------------------------------------------------------
# Blog Reaction Views
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def blog_react(request, slug):
    """React to a blog post (toggle: react again removes, change type updates)."""
    try:
        post = BlogPost.objects.get(slug=slug, status='published')
    except BlogPost.DoesNotExist:
        return Response(
            {'error': 'Blog post not found'}, status=status.HTTP_404_NOT_FOUND
        )

    serializer = BlogReactSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reaction_type = serializer.validated_data['reaction_type']

    existing = BlogReaction.objects.filter(post=post, user=request.user).first()

    if existing:
        if existing.reaction_type == reaction_type:
            # Same reaction → toggle off (unreact)
            existing.delete()
            return Response({
                'status': 'success',
                'message': 'Reaction removed',
                'action': 'removed',
            })
        else:
            # Different reaction → update
            existing.reaction_type = reaction_type
            existing.save()
            return Response({
                'status': 'success',
                'message': f'Reaction changed to {reaction_type}',
                'action': 'updated',
                'reaction_type': reaction_type,
            })

    reaction = BlogReaction.objects.create(
        post=post,
        user=request.user,
        reaction_type=reaction_type,
    )
    _notify_blog_reaction(reaction)

    return Response({
        'status': 'success',
        'message': f'Reacted with {reaction_type}',
        'action': 'created',
        'reaction_type': reaction_type,
    }, status=status.HTTP_201_CREATED)
