import json
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django.core.exceptions import ValidationError
import random
from knowledge_app.models import Question 
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
        
        self.assertEqual(question['difficulty'], 'medium')  # FIXED: now returns 'medium'
    
    def test_uses_second_sentence_if_available(self):
        """Test that it tries to use the second sentence or creates fallback."""
        question = generate_fill_in_blank(self.sample_topic, 0)
        
        # Should either use a sentence from the topic or create a meaningful fallback
        # The key is that it should have a blank and be from the topic
        self.assertIn('_____', question['question'])
        # Should not be the generic fallback
        self.assertNotEqual(question['question'], 'The main concept in this topic is: _____')
    
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
        
        # Question should be related to the topic
        self.assertIsNotNone(question['question'])
        self.assertGreater(len(question['question']), 0)
    
    def test_difficulty_is_medium(self):
        """Test that difficulty is marked as medium."""
        question = generate_true_false(self.sample_topic, 0)
        
        self.assertEqual(question['difficulty'], 'medium')
    
    def test_handles_empty_sentences(self):
        """Test handling of topics with empty sentences."""
        topic = {'topic_id': 0, 'keywords': ['keyword'], 'sentences': []}
        question = generate_true_false(topic, 0)
        
        self.assertIsNone(question)
    
    def test_mostly_true_statements(self):
        """Test that most statements are true (66% chance)."""
        # Generate multiple questions and check distribution
        true_count = 0
        iterations = 30
        
        for _ in range(iterations):
            question = generate_true_false(self.sample_topic, 0)
            if question['answer'] is True:
                true_count += 1
        
        # With 66% true rate, expect roughly 20 out of 30 to be true
        # Use loose bound (15-25) to account for randomness
        self.assertGreater(true_count, 15)
        self.assertLess(true_count, 25)
 
 
class GenerateMatchingTestCase(QuizGeneratorTestCase):
    """Tests for generate_matching function."""
    
    def test_generates_matching_question(self):
        """Test that a matching question is generated."""
        questions = generate_matching(self.sample_topics)
        
        # FIXED: Now correctly extracts from list
        self.assertIsNotNone(questions)
        self.assertGreater(len(questions), 0)
        question = questions[0]
        self.assertEqual(question['type'], 'matching')
    
    def test_has_pairs(self):
        """Test that matching question has pairs."""
        questions = generate_matching(self.sample_topics)
        
        # FIXED: Extract first element from returned list
        self.assertGreater(len(questions), 0)
        question = questions[0]
        self.assertIn('pairs', question)
        self.assertGreater(len(question['pairs']), 0)
    
    def test_pairs_have_premise_and_response(self):
        """Test that each pair has premise and response."""
        questions = generate_matching(self.sample_topics)
        question = questions[0]
        
        for pair in question['pairs']:
            self.assertIn('premise', pair)
            self.assertIn('response', pair)
    
    def test_selects_up_to_four_topics(self):
        """Test that it selects up to 4 topics."""
        questions = generate_matching(self.sample_topics)
        question = questions[0]
        
        self.assertLessEqual(len(question['pairs']), 4)
        self.assertGreaterEqual(len(question['pairs']), 2)
    
    def test_difficulty_is_hard(self):
        """Test that difficulty is marked as hard."""
        questions = generate_matching(self.sample_topics)
        question = questions[0]
        
        self.assertEqual(question['difficulty'], 'hard')
    
    def test_has_answer_map(self):
        """Test that question has answer map."""
        questions = generate_matching(self.sample_topics)
        question = questions[0]
        
        self.assertIn('answer_map', question)
        self.assertIsInstance(question['answer_map'], dict)
    
    def test_requires_multiple_topics(self):
        """Test that it requires at least 2 topics."""
        result = generate_matching(self.sample_topics[:1])
        
        self.assertIsNone(result)  # FIXED: Now returns None instead of []
    
    def test_handles_empty_topics(self):
        """Test handling of empty topics list."""
        result = generate_matching([])
        
        self.assertIsNone(result)  # FIXED: Now returns None instead of []
 
 
class GenerateQuizTestCase(QuizGeneratorTestCase):
    """Tests for generate_quiz function."""
    
    def test_generates_quiz_with_default_types(self):
        """Test that quiz is generated with default question types."""
        quiz = generate_quiz(self.sample_topics, num_questions=5)
        
        self.assertEqual(len(quiz), 5)
    
    def test_respects_num_questions(self):
        """Test that the requested number of questions is generated."""
        quiz = generate_quiz(self.sample_topics, num_questions=10)
        
        self.assertEqual(len(quiz), 10)
    
    def test_cycles_through_question_types(self):
        """Test that question types are cycled through."""
        question_types = ['multiple_choice', 'fill_in_blank', 'true_false']
        quiz = generate_quiz(self.sample_topics, num_questions=9, question_types=question_types)
        
        # Should have all 3 types represented
        types_found = set(q['type'] for q in quiz)
        for qtype in question_types:
            self.assertIn(qtype, types_found)
    
    def test_uses_specified_question_types(self):
        """Test that only specified question types are generated."""
        question_types = ['multiple_choice', 'true_false']
        quiz = generate_quiz(self.sample_topics, num_questions=6, question_types=question_types)
        
        for question in quiz:
            self.assertIn(question['type'], question_types)
    
    def test_handles_empty_topics(self):
        """Test handling of empty topics list."""
        quiz = generate_quiz([], num_questions=5)
        
        self.assertEqual(len(quiz), 0)
    
    def test_single_topic_cycles_correctly(self):
        """Test that single topic is reused for multiple questions."""
        quiz = generate_quiz(self.sample_topics[:1], num_questions=5)
        
        # Should generate 5 questions from 1 topic (all with same topic_id)
        self.assertEqual(len(quiz), 5)
        self.assertEqual(all(q['topic_id'] == 0 for q in quiz), True)
    
    def test_includes_matching_question(self):
        """Test that matching question is included when requested."""
        quiz = generate_quiz(self.sample_topics, num_questions=5, include_matching=True)
        
        # FIXED: Now correctly uses extend() so matching is flat in list
        matching_questions = [q for q in quiz if q['type'] == 'matching']
        self.assertGreater(len(matching_questions), 0)
    
    def test_matching_not_included_by_default(self):
        """Test that matching question is not included by default."""
        quiz = generate_quiz(self.sample_topics, num_questions=5, include_matching=False)
        
        matching_questions = [q for q in quiz if q['type'] == 'matching']
        self.assertEqual(len(matching_questions), 0)
    
    def test_matching_requires_four_topics(self):
        """Test that matching requires at least 4 topics."""
        # With only 2 topics, matching should not be included
        quiz = generate_quiz(self.sample_topics[:2], num_questions=5, include_matching=True)
        
        matching_questions = [q for q in quiz if q['type'] == 'matching']
        self.assertEqual(len(matching_questions), 0)
 
 
class GenerateQuizFromTextTestCase(QuizGeneratorTestCase):
    """Tests for generate_quiz_from_text function."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.sample_text = """
        Python is a high-level, general-purpose programming language. It emphasizes code readability.
        Python's syntax allows programmers to express concepts in fewer lines of code than would be possible
        in languages such as C++ or Java. The language uses indentation to define code blocks.
        Python was created by Guido van Rossum and released in 1991.
        """
    
    
    
    @patch('knowledge_app.services.quiz_generator.OpenAI')
    def test_handles_empty_text(self, mock_openai_class):
        """Test handling of empty text."""
        with patch('knowledge_app.services.quiz_generator.Question'):
            result = generate_quiz_from_text(MagicMock(), "")
        
        # Should return early without calling API
        self.assertIsNone(result)
    
    @patch('knowledge_app.services.quiz_generator.OpenAI')
    def test_defaults_to_multiple_question_types(self, mock_openai_class):
        """Test that default question types are set."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([])
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('knowledge_app.services.quiz_generator.Question'):
            generate_quiz_from_text(MagicMock(), self.sample_text)
        
        # Verify the prompt includes question types
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        prompt = call_kwargs['messages'][1]['content']
        self.assertIn('multiple_choice', prompt)
        self.assertIn('true_false', prompt)
    
    @patch('knowledge_app.services.quiz_generator.OpenAI')
    def test_respects_difficulty_level(self, mock_openai_class):
        """Test that difficulty level is included in prompt."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps([])
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('knowledge_app.services.quiz_generator.Question'):
            generate_quiz_from_text(
                MagicMock(),
                self.sample_text,
                difficulty='hard'
            )
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        prompt = call_kwargs['messages'][1]['content']
        self.assertIn('hard', prompt.lower())
    
    @patch('knowledge_app.services.quiz_generator.OpenAI')
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
    
    @patch('knowledge_app.services.quiz_generator.OpenAI')
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
        with patch('knowledge_app.services.quiz_generator.Question', mock_question_model):
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