Feature: Quiz Generation

  Scenario: User navigates to quiz page
    Given I am logged in
    When I visit the quizzes page
    Then I should see the quiz generation form

  Scenario: User sees all source choice options
    Given I am logged in
    When I visit the quizzes page
    Then I should see the existing PDF option
    And I should see the upload PDF option
    And I should see the paste text option

  Scenario: User generates a quiz from pasted text
    Given I am logged in
    When I submit the quiz form with text input
    Then a new quiz should be created