import pytest
from model_bakery import baker
from post.models import Post
from profiles.models import Profile


@pytest.fixture
def sample_payload():
    return {"author": baker.make(Profile), "content": "Sample content for this post."}


@pytest.mark.django_db
class TestPostModel:
    """Tests for the post model."""

    def test_create_post_successful(self, sample_payload):
        """Test creating a post is successful."""

        author = sample_payload.get("author")
        content = sample_payload.get("content")

        post = Post.objects.create(**sample_payload)

        assert post.author == author
        assert post.content == content
        assert str(post) == f'{content[:10]}... by "{author.full_name}"'

    def test_create_repost_successful(self, sample_payload):
        """Test creating a repost is successful."""
        author = baker.make(Profile)
        original_post = baker.make(Post, author=author)
        sample_payload.update({"original_post": original_post})

        repost = Post.objects.create(**sample_payload)

        assert repost.original_post == original_post
        assert repost.author == sample_payload.get("author")

    def test_reply_post_successful(self, sample_payload):
        """Test create reply to another post."""
        original_post = baker.make(Post)
        sample_payload.update({"reply_to": original_post})

        reply = Post.objects.create(**sample_payload)

        assert reply.reply_to == original_post
        assert reply.author == sample_payload.get("author")
