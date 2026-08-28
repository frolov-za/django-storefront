from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from products.integrations.together import TogetherAPIError, generate_completion


@override_settings(TOGETHER_API_KEY="test-key")
class TogetherCompletionTests(SimpleTestCase):
    @patch("products.integrations.together.requests.post")
    def test_reads_current_chat_response(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "Описание"}}]}
        post.return_value = response

        self.assertEqual(generate_completion("prompt"), "Описание")
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs["timeout"], 30)

    @patch("products.integrations.together.requests.post")
    def test_reads_legacy_response(self, post):
        response = Mock()
        response.json.return_value = {"output": {"choices": [{"text": "Описание"}]}}
        post.return_value = response

        self.assertEqual(generate_completion("prompt"), "Описание")

    @override_settings(TOGETHER_API_KEY=None)
    def test_requires_api_key(self):
        with self.assertRaises(TogetherAPIError):
            generate_completion("prompt")
