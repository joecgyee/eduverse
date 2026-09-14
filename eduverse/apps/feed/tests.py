from django.test import TestCase
from django.urls import reverse

from apps.users.models import StudentProfile, User, UserRole

from .models import Feed, FeedComment, Notification, NotificationType


def create_user(email):
    user = User.objects.create_user(email=email, password="pass1234", first_name="First", last_name="Last", role=UserRole.STUDENT)
    StudentProfile.objects.create(user=user, date_of_birth="2000-01-01")
    return user


class FeedListViewTests(TestCase):
    def setUp(self):
        self.user = create_user("list@example.com")
        for i in range(12):
            Feed.objects.create(author=self.user, content=f"Post {i}")

    def test_requires_login(self):
        self.assertEqual(self.client.get(reverse("feed:list")).status_code, 302)

    def test_pagination_limits_to_ten(self):
        self.client.login(email="list@example.com", password="pass1234")
        response = self.client.get(reverse("feed:list"))
        self.assertEqual(len(response.context["page_obj"].object_list), 10)

    def test_search_filters_content(self):
        self.client.login(email="list@example.com", password="pass1234")
        response = self.client.get(reverse("feed:list"), {"q": "Post 1"})
        contents = [f.content for f in response.context["page_obj"].object_list]
        self.assertTrue(all("Post 1" in c for c in contents))


class FeedCreateDeleteViewTests(TestCase):
    def setUp(self):
        self.author = create_user("author@example.com")
        self.other = create_user("other@example.com")

    def test_create_post(self):
        self.client.login(email="author@example.com", password="pass1234")
        self.client.post(reverse("feed:create"), {"content": "Hello world"})
        self.assertTrue(Feed.objects.filter(author=self.author, content="Hello world").exists())

    def test_author_can_delete_own_post(self):
        feed = Feed.objects.create(author=self.author, content="Delete me")
        self.client.login(email="author@example.com", password="pass1234")
        self.client.post(reverse("feed:delete", args=[feed.pk]))
        self.assertFalse(Feed.objects.filter(pk=feed.pk).exists())

    def test_non_author_cannot_delete_post(self):
        feed = Feed.objects.create(author=self.author, content="Protected")
        self.client.login(email="other@example.com", password="pass1234")
        response = self.client.post(reverse("feed:delete", args=[feed.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Feed.objects.filter(pk=feed.pk).exists())


class CommentCreateViewTests(TestCase):
    def setUp(self):
        self.author = create_user("post_author@example.com")
        self.commenter = create_user("commenter@example.com")
        self.feed = Feed.objects.create(author=self.author, content="A post")

    def test_comment_created_and_author_notified(self):
        self.client.login(email="commenter@example.com", password="pass1234")
        self.client.post(reverse("feed:comment_create", args=[self.feed.pk]), {"content": "Nice post!"})
        self.assertTrue(FeedComment.objects.filter(feed=self.feed, author=self.commenter).exists())
        self.assertTrue(
            Notification.objects.filter(recipient=self.author, type=NotificationType.FEED_COMMENT).exists()
        )
        def test_commenting_on_own_post_does_not_notify(self):
            self.client.login(email="post_author@example.com", password="pass1234")
            self.client.post(reverse("feed:comment_create", args=[self.feed.pk]), {"content": "My own comment"})
            self.assertFalse(Notification.objects.filter(recipient=self.author).exists())


class NotificationRedirectViewTests(TestCase):
    def setUp(self):
        self.user = create_user("notified@example.com")
        self.notification = Notification.objects.create(recipient=self.user, type=NotificationType.CHAT, message="Test")

    def test_marks_read_and_redirects(self):
        self.client.login(email="notified@example.com", password="pass1234")
        self.client.get(reverse("feed:notification_redirect", args=[self.notification.pk]))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_cannot_access_others_notification(self):
        create_user("intruder@example.com")
        self.client.login(email="intruder@example.com", password="pass1234")
        response = self.client.get(reverse("feed:notification_redirect", args=[self.notification.pk]))
        self.assertEqual(response.status_code, 404)