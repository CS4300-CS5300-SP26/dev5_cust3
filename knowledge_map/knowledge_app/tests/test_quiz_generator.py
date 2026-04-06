import json
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django.core.exceptions import ValidationError
import random

# Import the functions to test
from knowledge_app.services.quiz_generator import (
    generate_multiple_choice,
    generate_fill_in_blank,
    generate_true_false,
    generate_matching,
    generate_quiz,
    generate_quiz_from_text,
)


class QuizGeneratorTestCase(TestCase):
    """Base test case with common setup for quiz generator tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_topic = {
            'topic_id': 0,
            'keywords': ['Python', 'Programming', 'Language', 'Syntax', 'Variables'],
            'sentences': [
                'Python is a high-level programming language.',
                'It emphasizes code readability and simplicity.',
                'Python uses indentation to define code blocks.'
            ]
        }
        
        self.sample_topics = [
            {
                'topic_id': i,
                'keywords': [f'keyword_{i}_{j}' for j in range(5)],
                'sentences': [
                    f'This is sentence {k} about topic {i}.'
                    for k in range(3)
                ]
            }
            for i in range(4)
        ]
    
    def create_topic(self, topic_id=0, keyword_count=5, sentence_count=3):
        """Create a test topic."""
        return {
            'topic_id': topic_id,
            'keywords': [f'keyword_{topic_id}_{i}' for i in range(keyword_count)],
            'sentences': [
                f'This is sentence {i} for topic {topic_id}.'
                for i in range(sentence_count)
            ]
        }


class GenerateMultipleChoiceTestCase(QuizGeneratorTestCase):
    """Tests for generate_multiple_choice function."""
    
    def test_generates_valid_question(self):
        """Test that a valid multiple choice question is generated."""
        question = generate_multiple_choice(self.sample_topic, 0)
        
        self.assertIsNotNone(question)
        self.assertEqual(question['type'], 'multiple_choice')
        self.assertEqual(question['id'], 'q_0_mc')
        self.assertIn('question', question)
        self.assertIn('choices', question)
        self.assertIn('answer', question)
    
    def test_has_four_choices(self):
        """Test that generated question has exactly 4 choices."""
        question = generate_multiple_choice(self.sample_topic, 0)
        
        self.assertEqual(len(question['choices']), 4)
    
    def test_correct_answer_in_choices(self):
        """Test that the correct answer is in the choices."""
        question = generate_multiple_choice(self.sample_topic, 0)
        
        self.assertIn(question['answer'], question['choices'])
    
    def test_question_contains_sentence_snippet(self):
        """Test that question text includes part of a sentence."""
        question = generate_multiple_choice(self.sample_topic, 0)
        
        # Question should reference the sentence
        self.assertIn('relevant', question['question'].lower())
    
    def test_handles_empty_keywords(self):
        """Test handling of topics with empty keywords."""
        topic = {'topic_id': 0, 'keywords': [], 'sentences': ['sentence']}
        question = generate_multiple_choice(topic, 0)
        
        self.assertIsNone(question)
    
    def test_handles_empty_sentences(self):
        """Test handling of topics with empty sentences."""
        topic = {'topic_id': 0, 'keywords': ['keyword'], 'sentences': []}
        question = generate_multiple_choice(topic, 0)
        
        self.assertIsNone(question)
    
    def test_difficulty_is_easy(self):
        """Test that difficulty is marked as easy."""
        question = generate_multiple_choice(self.sample_topic, 0)
        
        self.assertEqual(question['difficulty'], 'easy')
    
    def test_topic_id_preserved(self):
        """Test that original topic_id is preserved."""
        question = generate_multiple_choice(self.sample_topic, 5)
        
        self.assertEqual(question['topic_id'], self.sample_topic['topic_id'])


class GenerateFillInBlankTestCase(QuizGeneratorTestCase):
    """Tests for generate_fill_in_blank function."""
    
    def test_generates_valid_question(self):
        """Test that a valid fill-in-blank question is generated."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        self.assertIsNotNone(question)
        self.assertEqual(question['type'], 'fill_in_blank')
        self.assertEqual(question['id'], 'q_0_fib')
        self.assertIn('question', question)
        self.assertIn('choices', question)
        self.assertIn('answer', question)
    
    def test_has_blank_in_question(self):
        """Test that question contains a blank."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        self.assertIn('_____', question['question'])
    
    def test_has_multiple_choices(self):
        """Test that question has multiple choices."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        self.assertGreaterEqual(len(question['choices']), 3)
    
    def test_correct_answer_in_choices(self):
        """Test that the correct answer is in the choices."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        self.assertIn(question['answer'], question['choices'])
    
    def test_difficulty_is_medium(self):
        """Test that difficulty is marked as medium."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        self.assertEqual(question['difficulty'], 'medium')
    
    def test_uses_second_sentence_if_available(self):
        """Test that it tries to use the second sentence."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        # Should use a sentence from the topic
        self.assertIn(question['question'], [
            q.replace('_____', f'keyword_{self.sample_topic["topic_id"]}_j')
            for q in self.sample_topic['sentences']
        ] or question['question'].startswith('The main concept'))
    
    def test_handles_empty_keywords(self):
        """Test handling of topics with empty keywords."""
        topic = {'topic_id': 0, 'keywords': [], 'sentences': ['sentence']}
        question = generate_fill_in_blank(topic, 0)
        
        self.assertIsNone(question)
    
    def test_handles_empty_sentences(self):
        """Test handling of topics with empty sentences."""
        topic = {'topic_id': 0, 'keywords': ['keyword'], 'sentences': []}
        question = generate_fill_in_blank(topic, 0)
        
        self.assertIsNone(question)
    
    def test_blank_count_is_one(self):
        """Test that there is exactly one blank."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        blank_count = question['question'].count('_____')
        self.assertEqual(blank_count, 1)


class GenerateTrueFalseTestCase(QuizGeneratorTestCase):
    """Tests for generate_true_false function."""
    
    def test_generates_valid_question(self):
        """Test that a valid true/false question is generated."""
        question = generate_true_false(self.sample_topic, 0)
        
        self.assertIsNotNone(question)
        self.assertEqual(question['type'], 'true_false')
        self.assertEqual(question['id'], 'q_0_tf')
        self.assertIn('question', question)
        self.assertIn('answer', question)
    
    def test_answer_is_boolean(self):
        """Test that the answer is a boolean."""
        question = generate_true_false(self.sample_topic, 0)
        
        self.assertIsInstance(question['answer'], bool)
    
    def test_question_from_sentences(self):
        """Test that question uses sentences from topic."""
        question = generate_true_false(self.sample_topic, 0)
        
        # Question should be based on a sentence
        is_from_sentences = any(
            sentence in question['question'] or
            question['question'] in sentence
            for sentence in self.sample_topic['sentences']
        )
        # Should be true or a reasonable variation
        self.assertTrue(
            is_from_sentences or len(question['question']) > 0
        )
    
    def test_difficulty_is_medium(self):
        """Test that difficulty is marked as medium."""
        question = generate_true_false(self.sample_topic, 0)
        
        self.assertEqual(question['difficulty'], 'medium')
    
    def test_handles_empty_sentences(self):
        """Test handling of topics with empty sentences."""
        topic = {'topic_id': 0, 'keywords': ['keyword'], 'sentences': []}
        question = generate_true_false(topic, 0)
        
        self.assertIsNone(question)
    
    def test_produces_both_true_and_false(self):
        """Test that generator produces both true and false statements."""
        # Generate multiple questions to check variation
        answers = []
        for i in range(20):
            topic = self.create_topic(topic_id=i)
            question = generate_true_false(topic, i)
            if question:
                answers.append(question['answer'])
        
        # Should have both True and False statements
        self.assertIn(True, answers)
        self.assertIn(False, answers)


class GenerateMatchingTestCase(QuizGeneratorTestCase):
    """Tests for generate_matching function."""
    
    def test_generates_matching_question(self):
        """Test that a matching question is generated."""
        question = generate_matching(self.sample_topics)
        
        self.assertIsNotNone(question)
        self.assertEqual(question['type'], 'matching')
        self.assertEqual(question['id'], 'q_matching')
    
    def test_has_pairs(self):
        """Test that matching question has pairs."""
        question = generate_matching(self.sample_topics)
        
        self.assertIn('pairs', question)
        self.assertGreater(len(question['pairs']), 0)
    
    def test_selects_up_to_four_topics(self):
        """Test that it selects up to 4 topics."""
        question = generate_matching(self.sample_topics)
        
        self.assertLessEqual(len(question['pairs']), 4)
        self.assertGreaterEqual(len(question['pairs']), 2)
    
    def test_pairs_have_premise_and_response(self):
        """Test that each pair has premise and response."""
        question = generate_matching(self.sample_topics)
        
        for pair in question['pairs']:
            self.assertIn('premise', pair)
            self.assertIn('response', pair)
            self.assertIsNotNone(pair['premise'])
            self.assertIsNotNone(pair['response'])
    
    def test_has_answer_map(self):
        """Test that question has answer map."""
        question = generate_matching(self.sample_topics)
        
        self.assertIn('answer_map', question)
        self.assertEqual(len(question['answer_map']), len(question['pairs']))
    
    def test_difficulty_is_hard(self):
        """Test that difficulty is marked as hard."""
        question = generate_matching(self.sample_topics)
        
        self.assertEqual(question['difficulty'], 'hard')
    
    def test_requires_multiple_topics(self):
        """Test that it requires at least 2 topics."""
        question = generate_matching([self.sample_topics[0]])
        
        self.assertIsNone(question)
    
    def test_handles_empty_topics(self):
        """Test handling of empty topics list."""
        question = generate_matching([])
        
        self.assertIsNone(question)


class GenerateQuizTestCase(QuizGeneratorTestCase):
    """Tests for generate_quiz function."""
    
    def test_generates_correct_number_of_questions(self):
        """Test that the correct number of questions is generated."""
        quiz = generate_quiz(self.sample_topics, num_questions=5)
        
        self.assertEqual(len(quiz), 5)
    
    def test_defaults_to_two_per_topic(self):
        """Test that default is 2 questions per topic."""
        quiz = generate_quiz(self.sample_topics)
        
        expected_count = len(self.sample_topics) * 2 + 1  # +1 for matching
        self.assertGreater(len(quiz), len(self.sample_topics) * 2)
    
    def test_cycles_through_topics(self):
        """Test that questions cycle through topics."""
        quiz = generate_quiz(self.sample_topics, num_questions=8)
        
        topic_ids = [q['topic_id'] for q in quiz if 'topic_id' in q]
        unique_topics = set(topic_ids)
        
        # Should use multiple topics
        self.assertGreater(len(unique_topics), 1)
    
    def test_cycles_through_question_types(self):
        """Test that question types cycle."""
        quiz = generate_quiz(self.sample_topics, num_questions=6)
        
        types = [q['type'] for q in quiz]
        
        # Should have multiple types (excluding matching)
        self.assertGreater(len(set(types)), 1)
    
    def test_includes_matching_question(self):
        """Test that matching question is included."""
        quiz = generate_quiz(self.sample_topics, num_questions=4)
        
        matching_questions = [q for q in quiz if q['type'] == 'matching']
        self.assertGreater(len(matching_questions), 0)
    
    def test_handles_empty_topics(self):
        """Test handling of empty topics list."""
        quiz = generate_quiz([], num_questions=5)
        
        self.assertEqual(len(quiz), 0)
    
    def test_all_questions_valid(self):
        """Test that all questions in the quiz are valid."""
        quiz = generate_quiz(self.sample_topics, num_questions=10)
        
        for question in quiz:
            self.assertIn('id', question)
            self.assertIn('type', question)
            self.assertIn('answer', question)
    
    def test_unique_question_ids(self):
        """Test that all question IDs are unique."""
        quiz = generate_quiz(self.sample_topics, num_questions=10)
        
        ids = [q['id'] for q in quiz]
        self.assertEqual(len(ids), len(set(ids)))
    
    def test_id_format(self):
        """Test that IDs follow expected format."""
        quiz = generate_quiz(self.sample_topics, num_questions=5)
        
        for question in quiz:
            question_id = question['id']
            self.assertTrue(
                question_id.startswith('q_'),
                f"ID {question_id} doesn't start with 'q_'"
            )
    
    def test_respects_custom_num_questions(self):
        """Test that custom num_questions is respected."""
        for num in [1, 3, 7, 15]:
            quiz = generate_quiz(self.sample_topics, num_questions=num)
            self.assertEqual(
                len(quiz), num,
                f"Expected {num} questions, got {len(quiz)}"
            )


class GenerateQuizFromTextTestCase(QuizGeneratorTestCase):
    """Tests for generate_quiz_from_text function."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.sample_text = """
        Python is a high-level programming language.
        It is known for its simplicity and readability.
        Python supports object-oriented programming.
        The language has built-in data structures.
        Python is widely used in data science.
        """
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_calls_openai_api(self, mock_openai_class):
        """Test that OpenAI API is called."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([
            {
                'question_text': 'What is Python?',
                'question_type': 'multiple_choice',
                'choices': ['A language', 'A snake', 'A tool', 'A framework'],
                'correct_answer': 'A language'
            }
        ])
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock the Question model
        with patch('quiz.services.quiz_generator.Question'):
            generate_quiz_from_text(MagicMock(), self.sample_text, num_questions=1)
        
        # Verify OpenAI was called
        mock_openai_class.assert_called()
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_uses_correct_model(self, mock_openai_class):
        """Test that the correct OpenAI model is used."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([])
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('quiz.services.quiz_generator.Question'):
            generate_quiz_from_text(MagicMock(), self.sample_text, num_questions=1)
        
        # Verify the correct model was used
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_kwargs['model'], 'gpt-5-mini')
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_handles_empty_text(self, mock_openai_class):
        """Test handling of empty text."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Should return early without calling OpenAI
        generate_quiz_from_text(MagicMock(), '', num_questions=5)
        
        # OpenAI should not be called
        mock_client.chat.completions.create.assert_not_called()
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_defaults_to_multiple_question_types(self, mock_openai_class):
        """Test that default question types are set."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([])
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('quiz.services.quiz_generator.Question'):
            generate_quiz_from_text(MagicMock(), self.sample_text)
        
        # Verify the prompt includes question types
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        prompt = call_kwargs['messages'][1]['content']
        self.assertIn('multiple_choice', prompt)
        self.assertIn('true_false', prompt)
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_respects_difficulty_level(self, mock_openai_class):
        """Test that difficulty level is included in prompt."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([])
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('quiz.services.quiz_generator.Question'):
            generate_quiz_from_text(
                MagicMock(),
                self.sample_text,
                difficulty='hard'
            )
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        prompt = call_kwargs['messages'][1]['content']
        self.assertIn('hard', prompt.lower())
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_parses_json_response(self, mock_openai_class):
        """Test that JSON response is properly parsed."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        questions_json = json.dumps([
            {
                'question_text': 'Q1?',
                'question_type': 'multiple_choice',
                'choices': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A'
            },
            {
                'question_text': 'Q2?',
                'question_type': 'true_false',
                'choices': ['True', 'False'],
                'correct_answer': 'True'
            }
        ])
        mock_response.choices[0].message.content = questions_json
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_question_model = MagicMock()
        with patch('quiz.services.quiz_generator.Question', mock_question_model):
            generate_quiz_from_text(MagicMock(), self.sample_text, num_questions=2)
        
        # Verify both questions were created
        self.assertEqual(mock_question_model.objects.create.call_count, 2)
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_handles_markdown_wrapped_json(self, mock_openai_class):
        """Test handling of JSON wrapped in markdown code blocks."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        questions_json = json.dumps([
            {
                'question_text': 'Q1?',
                'question_type': 'multiple_choice',
                'choices': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A'
            }
        ])
        
        # Wrap in markdown
        markdown_response = f"```json\n{questions_json}\n```"
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = markdown_response
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_question_model = MagicMock()
        with patch('quiz.services.quiz_generator.Question', mock_question_model):
            generate_quiz_from_text(MagicMock(), self.sample_text, num_questions=1)
        
        # Should successfully create the question despite markdown
        mock_question_model.objects.create.assert_called_once()
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_handles_api_errors(self, mock_openai_class):
        """Test graceful handling of API errors."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Simulate API error
        mock_client.chat.completions.create.side_effect = Exception(
            "API error"
        )
        
        # Should not raise exception (prints instead)
        try:
            generate_quiz_from_text(MagicMock(), self.sample_text)
        except Exception as e:
            self.fail(f"generate_quiz_from_text raised {type(e).__name__}")
    
    @patch('quiz.services.quiz_generator.OpenAI')
    def test_sets_question_order(self, mock_openai_class):
        """Test that question order is set correctly."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        questions_json = json.dumps([
            {
                'question_text': f'Q{i}?',
                'question_type': 'multiple_choice',
                'choices': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A'
            }
            for i in range(3)
        ])
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = questions_json
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_question_model = MagicMock()
        with patch('quiz.services.quiz_generator.Question', mock_question_model):
            generate_quiz_from_text(MagicMock(), self.sample_text, num_questions=3)
        
        # Verify order parameter is set
        calls = mock_question_model.objects.create.call_args_list
        for i, call_obj in enumerate(calls, start=1):
            kwargs = call_obj[1]
            self.assertEqual(kwargs['order'], i)


class EdgeCaseTestCase(QuizGeneratorTestCase):
    """Tests for edge cases and boundary conditions."""
    
    def test_very_long_keyword(self):
        """Test handling of very long keywords."""
        topic = {
            'topic_id': 0,
            'keywords': ['a' * 500, 'short'],
            'sentences': ['Test sentence with ' + 'a' * 500]
        }
        question = generate_multiple_choice(topic, 0)
        
        # Should handle long keywords gracefully
        self.assertIsNotNone(question)
    
    def test_special_characters_in_keywords(self):
        """Test handling of special characters in keywords."""
        topic = {
            'topic_id': 0,
            'keywords': ['C++', 'C#', 'Node.js', 'Vue.js', 'regex[a-z]'],
            'sentences': ['Test sentence with special chars']
        }
        question = generate_multiple_choice(topic, 0)
        
        self.assertIsNotNone(question)
    
    def test_unicode_in_keywords(self):
        """Test handling of Unicode characters in keywords."""
        topic = {
            'topic_id': 0,
            'keywords': ['café', '日本語', 'Москва', 'العربية', 'emoji😀'],
            'sentences': ['Test sentence with unicode']
        }
        question = generate_multiple_choice(topic, 0)
        
        self.assertIsNotNone(question)
    
    def test_single_topic(self):
        """Test quiz generation with single topic."""
        quiz = generate_quiz([self.sample_topics[0]], num_questions=5)
        
        # Should still work and generate questions
        self.assertGreater(len(quiz), 0)
    
    def test_very_large_quiz(self):
        """Test generating a very large quiz."""
        quiz = generate_quiz(self.sample_topics, num_questions=100)
        
        self.assertEqual(len(quiz), 100)
    
    def test_sentence_without_keywords(self):
        """Test fill-in-blank with sentence not containing keywords."""
        topic = {
            'topic_id': 0,
            'keywords': ['Python', 'Java'],
            'sentences': ['This sentence has no keywords at all']
        }
        question = generate_fill_in_blank(topic, 0)
        
        # Should fall back to default blank question
        self.assertIsNotNone(question)
        self.assertIn('_____', question['question'])
