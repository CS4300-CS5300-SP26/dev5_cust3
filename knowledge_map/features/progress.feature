Feature: Progress and Mastery Page

  Scenario: User navigates to progress page
    Given I am logged in
    When I visit the progress page
    Then I should see the mastery progress page

  Scenario: User sees not attempted status with no quiz attempts
    Given I am logged in
    And I have a quiz with no attempts
    When I visit the progress page
    Then I should see the not attempted status

  Scenario: User sees mastered status after scoring 80 or above
    Given I am logged in
    And I have a quiz with a score of 80
    When I visit the progress page
    Then I should see the mastered status