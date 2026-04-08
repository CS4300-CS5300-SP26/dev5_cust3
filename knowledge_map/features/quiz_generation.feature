Feature: Quiz Generation from Topics and Text
  As an educator
  I want to generate quiz questions from topics or raw text
  So that students can test their knowledge

  Background:
    Given I have sample topics with keywords and sentences

  Scenario: Generate multiple choice questions from topics
    When I generate quiz with 2 questions of type multiple_choice
    Then I should get 2 questions in the quiz
    And each question should have 4 choices
    And each question should have 1 correct answer

  Scenario: Generate fill-in-blank questions from topics
    When I generate quiz with 2 questions of type fill_in_blank
    Then I should get 2 questions in the quiz
    And each question should have a blank marked with "_____"
    And each question should have at least 3 answer choices


  Scenario: Generate mixed question types
    When I generate quiz with 3 questions of mixed types
    Then I should get 3 questions in the quiz
    And the quiz should contain different question types
    And each question should be valid

  Scenario: Handle empty topics gracefully
    When I generate quiz from empty topics list
    Then the quiz should be empty
    And no errors should occur

  Scenario: Generate quiz from raw text using OpenAI
    When I have raw text about "Python programming"
    And I request 5 quiz questions
    Then OpenAI should be called with the text
    And I should get 5 questions back
    And each question should have a question_text and correct_answer

  Scenario: Generate questions with different difficulty levels
    When I request quiz questions with difficulty "easy"
    Then questions should be simple and test basic recall
    And wrong answers should be clearly incorrect


  Scenario: Handle missing or incomplete topic data
    When I have topics with missing keywords or sentences
    Then the generator should handle gracefully
    And only valid questions should be generated
    And no exceptions should be raised

  Scenario: Question IDs are unique
    When I generate a quiz with 10 questions
    Then each question should have a unique ID
    And all IDs should follow the naming convention

  Scenario: Generate questions cycling through topics
    When I have 3 topics
    And I generate 9 questions
    Then each topic should contribute equally to the quiz
    And questions should be distributed across topics
